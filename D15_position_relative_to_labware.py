from opentrons import protocol_api

metadata = {
    "protocolName": "D15:Well positions的设置与两种group_step的注释方式",
    "author": "Your Name"
}#都是字典类型

requirements = {
    "robotType": "Flex",
    "apiLevel": "2.29"
}#都是字典类型


def run(protocol: protocol_api.ProtocolContext):
    

    # 1. Load a tiprack for 50/200 µL tips
    tips_50 = protocol.load_labware(
        "opentrons_flex_96_tiprack_50ul","C2")
    tips_200 = protocol.load_labware(
        "opentrons_flex_96_tiprack_200ul","C3")
    # 2. Load 96-well plates
    plate = protocol.load_labware(
        "corning_96_wellplate_360ul_flat","D1")
    plate_384 = protocol.load_labware(
        "corning_384_wellplate_112ul_flat","D2") #这里混进来了一个384孔板
    # 3. Load 8-channel/96-channel pipettes：见Loading Pipettes页面
    pipette_1chan = protocol.load_instrument(
        instrument_name="flex_1channel_50",
        mount="left",
        tip_racks=[tips_200])
    pipette_8chan = protocol.load_instrument(
        instrument_name="flex_8channel_50",
        mount="right",
        tip_racks=[tips_50])
    # 4. Load trash
    trash = protocol.load_trash_bin("A3")
    
    # 5. Well positions
    #Every well on every piece of labware has four addressable positions: top, bottom, center, and meniscus.
    #The top, bottom, and center positions are determined by the labware definition and what the labware is loaded on top of. The meniscus position is determined by the height of the liquid inside a well. You can use these positions as-is or calculate other positions relative to them.
    #建立step group，方便后续管理
    platetop=protocol.create_and_start_step_group(
        name = "Top",description = "It returns a position level with the top of the well, centered in both horizontal directions.")
    plate["A1"].top()  # the top center of the well
    #This is a good position to use for a blow out operation or an activity where you don't want the tip to contact the liquid. PCR程序
    #In addition, you can adjust the height of this position with the optional argument z, which is measured in mm. Positive z numbers move the position up, negative z numbers move it down.
    plate["A1"].top(z=1)  # 1 mm above the top center of the well
    plate["A1"].top(z=-1) # 1 mm below the top center of the well
    platetop.end_group()
    
    platebottom=protocol.create_and_start_step_group(
        name = "Bottom",description = "It returns a position level with the bottom of the well, centered in both horizontal directions. ")
    plate["A2"].bottom()  # the bottom center of the well
    #This is a good position for aspirating liquid or an activity where you want the tip to contact the liquid. 
    plate["A2"].bottom(z=1)  # 1 mm above the top center of the well
    plate["A2"].bottom(z=-1) # 1 mm below the top center of the well.  This may be dangerous!
    platebottom.end_group()
    
    platecenter=protocol.create_and_start_step_group(
        name = "Center",description = "It returns a position centered in the well both vertically and horizontally.")
     #This can be a good place to start for precise control of positions within the well for unusual or custom labware.
    plate["A3"].center() # the vertical and horizontal center of the well
    platecenter.end_group()
    
    platemeniscus=protocol.create_and_start_step_group(
        name = "Meniscus",description = "It returns a position at the surface of liquid, or meniscus, inside a well.")
    plate["A4"].meniscus(z=-1, target= "end") 
    # 1 mm below the meniscus of liquid inside the well
    #The liquid meniscus in a well changes during aspirating or dispensing, so you'll also need to specify a target position relative to the meniscus. Each position target is useful in different scenarios（原因就是因为加样后液面会上升）:
    #Set target="start" to target the existing liquid meniscus in the destination well before a dispense. #加/吸样前
    #Set target="end" to ensure the pipette stays submerged while aspirating, or to avoid touching liquid in the destination well while dispensing. #加/吸样后
    
    #You can use the optional location and end_location parameters of the aspirate() and dispense() methods to pipette relative to the liquid meniscus as it changes: 
    '''
    需要指明的是：
    To use the meniscus() method, you'll first need to specify the starting liquid volume with Labware.load_liquid() or probe for liquid with measure_liquid_height().
    Detecting liquid in a well requires pipette sensors, so you can only measure liquid height with a Flex pipette. 
    唉，我发现Labware.load_liquid() 这个参数的门门道道还挺多的。
    '''
    #方法一：在协议中“加载液体”（推荐用于已知体积）（Labware.load_liquid()）
    # 先定义液体（例如水）
    water = protocol.define_liquid(
        name="Water",
        description="Buffer",
        display_color="#EFA092"
    )
    # 告诉机器人：A3 和 A4 孔里有液体，体积分别是多少
    # 注意：你需要根据实际情况填写体积
    for well in plate.columns()[3]:
        well.load_liquid(liquid=water, volume=100) 
    # 之后你再调用 meniscus 就不会报错了
    pipette_8chan.pick_up_tip()
    pipette_8chan.aspirate(
        volume=30,
        location=plate["A4"].meniscus(z=-1, target="start"),
        end_location=plate["A4"].meniscus(z=-2, target="end")
    )
    pipette_8chan.dispense(
        volume=30,
        location=plate["A5"])
    pipette_8chan.drop_tip()
    #Here, the pipette tip stays at 1 mm below the liquid meniscus, regardless of changes in liquid height during the aspirate. For more, see the aspirate and dispense sections.
    #别想着让pipette transfer一点liquid到新well中去就可以骗过去了，不行的，必须用load_liquid去指定。
    #方法二：让移液器“探测液面”（用于未知体积）（Pipette.measure_liquid_height()）
    # 先装枪头
    pipette_8chan.pick_up_tip()
    # 探测 A4 孔的液面高度
    pipette_8chan.measure_liquid_height(plate["A6"])
    # 现在可以使用 meniscus 了
    pipette_8chan.aspirate(
        volume=20,
        location=plate["A6"].meniscus(z=-3, target="start"),
        end_location=plate["A6"].meniscus(z=-4, target="end")
    )
    pipette_8chan.dispense(
        volume=20,
        location=plate["A7"])
    pipette_8chan.drop_tip()
    
    platemeniscus.end_group()
    
    # 6. Default positions
    #By default, your robot will aspirate and dispense 1 mm above the bottom of wells. This default clearance may not be suitable for some labware geometries, liquids, or protocols. You can change this value based on your labware with the Well.bottom() method and the z argument, though it can be cumbersome to do so repeatedly.
    #If you need to change the aspiration or dispensing height for multiple operations, specify the distance in mm from the well bottom with the InstrumentContext.well_bottom_clearance object（这个参数是从孔底开始算起的）. It has two attributes: well_bottom_clearance.aspirate and well_bottom_clearance.dispense. These change the aspiration height and dispense height, respectively. 设置默认加样高度，PCR程序中。设置一次多次实验。
    #Modifying these attributes will affect all subsequent aspirate and dispense actions performed by the attached pipette, even those executed as part of a transfer() operation（由于是总体高度设置，所以transfer()也会适用）. This snippet from a sample protocol demonstrates how to work with and change the default clearance:
    #还有一种group_step的函数块注释方式：
    with protocol.group_steps(name="Default positions", description="If you need to change the aspiration or dispensing height for multiple operations, specify the distance in mm from the well bottom with the InstrumentContext.well_bottom_clearance object"):
        pipette_1chan.pick_up_tip()
        # aspirate 1 mm above the bottom of the well (default)
        pipette_1chan.aspirate(50, plate["C3"])
        # dispense 1 mm above the bottom of the well (default)
        pipette_1chan.dispense(50, plate["C3"])
        
        # change clearance for aspiration to 2 mm
        pipette_1chan.well_bottom_clearance.aspirate = 2
        # aspirate 2 mm above the bottom of the well
        pipette_1chan.aspirate(50, plate["D3"])
        # still dispensing 1 mm above the bottom
        pipette_1chan.dispense(50, plate["D3"])
        
        pipette_1chan.aspirate(50, plate["E3"])
        # change clearance for dispensing to 10 mm      
        pipette_1chan.well_bottom_clearance.dispense = 10
        # dispense high above the well
        pipette_1chan.dispense(50, plate["E3"])
        pipette_1chan.drop_tip()
    
    # 7. Position relative to trash containers
    #You can adjust the position of the pipette center with the TrashBin.top() and WasteChute.top() methods. These methods allow adjustments along the x-, y-, and z-axes. 
    #需要注意：In contrast, Well.top(), covered above, only allows z-axis adjustment. With no adjustments, the "top" position is centered on the x- and y-axes and is just below the opening of the trash container.
    #Another difference between the trash container top() methods and Well.top() is that they return an object of the same type, not a Location. This helps prevent performing undesired actions in trash containers. For example, you can aspirate at a location or from a well, but not from a trash container. On the other hand, you can blow out at a location, well, trash bin, or waste chute.
    #翻译过来就是，在 Opentrons 中，trash.top(z=10) 这种写法本身不能直接用于 drop_tip 来指定落枪头的位置。drop_tip 需要的是一个可用于丢弃枪头的“位置对象”，而 trash.top() 返回的只是用于移动或吹气的参考点。和上述的plate["A1"].top(z=1)是不一样的。
    with protocol.group_steps(name="Position relative to trash containers", description="You can adjust the position of the pipette center with the TrashBin.top() and WasteChute.top() methods"):
        trash.top(z=10)  # 10 mm higher
        trash.top(y=10)  # 10 mm towards back, default height
        #想要特定位置打掉枪头
        pipette_1chan.pick_up_tip()
        # 移动到垃圾桶上方，并额外抬高 10mm
        pipette_1chan.move_to(trash.top(x=4,y=5,z=10))
        # 或者在此位置吹气
        pipette_1chan.blow_out(trash.top(x=6,y=8,z=9))
        # 或者在此位置吹气
        pipette_1chan.drop_tip(trash.top(x=11,y=12,z=3))
        
    
    
    
    
    
    