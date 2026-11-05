from opentrons import protocol_api

metadata = {
    "protocolName": "D14:Multi-channel pipette movement学习",
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
    '''
    Because of its size, the Flex 96-Channel Pipette requires the left and right pipette mounts. You cannot use this pipette with 1- or 8-Channel Pipette in the same protocol or when these instruments are attached to the robot. Load the 96-channel pipette as follows:
    pipette_96chan = protocol.load_instrument(
        instrument_name="flex_96channel_200",
        tip_racks=[tips_200])
    遇到问题还是直接问DS老师吧，自己摸索半天不如直接问有效率。
    '''
    # 4. Load trash
    trash = protocol.load_trash_bin(
        "A3")
    
    # 5. 8-channel, 96-well plate example
    
    #With the backmost pipette channel above location A1 on the tip rack, all eight channels are above the eight tip rack wells in column 1.
    pipette_8chan.pick_up_tip()
    pipette_8chan.drop_tip()
    pipette_8chan.pick_up_tip(tips_50.wells()[20])#取第3列中随便一个格子就是直接取第3列的tips；也就是说pipette_8chan.pick_up_tip(tips_50["A3"])也是可以的
    #If specified, location should be an instance of `types.Location` (e.g. the return value from `Well.top()`), `Labware` or `Well` (e.g. `tiprack.wells()[0]`).所以像这种对着一整列的，不能这么用。pipette_8chan.pick_up_tip(tips_50.columns()[2])
    
    #After picking up a tip, let’s tell the robot to aspirate 300 µL from the well plate at location A2:
    pipette_8chan.aspirate(volume=30, location=plate["A2"])
    #With the backmost pipette tip above location A2 on the well plate, all eight channels are above the eight wells in column 2.看到没，这里也是直接取某一个某一个特定的孔来代表一整列。所以你就知道，当时pick_up_tip的时候也是可以用这种方法的。
    
    #Finally, let’s tell the robot to dispense 300 µL into the well plate at location A3:
    pipette_8chan.dispense(volume=30, location=plate["A3"].top())
    #With the backmost pipette tip above location A3, all eight channels are above the eight wells in column 3. The pipette will dispense liquid into all the wells simultaneously.
    #模拟器上亮点只有你写的那个孔plate["A3"]，但是鼠标悬停其实能看到所有的孔其实都加上了
    
    #所以如果我不对A这一行应该也是一样的
    pipette_8chan.aspirate(volume=13, location=plate["D3"])
    pipette_8chan.dispense(volume=13, location=plate["E4"])
    #奇怪，其实这里吸plate["D3"]和吸plate["A3"]是一样的，因为8-channel都是吸一列，但是我用dispense到plate["A4"]，simulation就能显示4列有13ul，而写dispense到plate["E4"]，simulation就不显示，可能是模拟器的问题吧。
    pipette_8chan.drop_tip()
    
    # 6. 8-channel, 384-well plate example
    
    #In general, you should specify wells in the first row of a well plate when using multi-channel pipettes. An exception to this rule is when using 384-well plates. The greater well density means the nozzles of a multi-channel pipette can only access every other well in a column. Specifying well A1 accesses every other well starting with the first (rows A, C, E, G, I, K, M, and O). Similarly, specifying well B1 also accesses every other well, but starts with the second (rows B, D, F, H, J, L, N, and P).
    #还记得二楼平台培训Multidrop的时候说的16通道加细胞的方法吗，由于喷嘴之间有间距，所以加样的时候都是间隔加样的。所以在加样的时候一定要好好规划。
    
    #To demonstrate these concepts, let’s write a protocol that uses a Flex 8-Channel Pipette and a 384-well plate. We’ll then aspirate and dispense a liquid to different locations on the same well plate. To start, let’s load a pipette in the right mount and add our labware.
    pipette_8chan.pick_up_tip(tips_50["A4"])
    #With the backmost pipette channel above location A4 on the tip rack, all eight channels are above the eight tip rack wells in column 4.
    
    #After picking up a tip, let’s tell the robot to aspirate 100 µL from the well plate at location A1:
    pipette_8chan.aspirate(volume=25, location=plate_384["A1"])
    # The eight pipette channels will only aspirate from every other well in the column: A1, C1, E1, G1, I1, K1, M1, and O1..
    
    #Finally, let’s tell the robot to dispense 100 µL into the well plate at location B1:
    pipette_8chan.dispense(volume=25, location=plate_384["B1"])
    #The eight pipette channels will only dispense into every other well in the column: B1, D1, F1, H1, J1, L1, N1, and P1.
    pipette_8chan.drop_tip()
    pipette_8chan.pick_up_tip() #从C2板位的Opentrons Flex 96 Tip Rack 50 µL的A2 - H2孔中拾取吸头，即默认从最左手边的枪头开始插起


    
    # 7. Pipette flow rates
    #原来真的有一节专门讲设置flow rates啊
    #Opentrons pipettes have their own default flow rates. The API lets you change the flow rate on a loaded InstrumentContext by altering the InstrumentContext.flow_rate properties listed below.
    #Aspirate: InstrumentContext.flow_rate.aspirate
    #Dispense: InstrumentContext.flow_rate.dispense
    #Blow out: InstrumentContext.flow_rate.blow_out
    
    #Let’s tell the robot to aspirate, dispense, and blow out the liquid using default flow rates. 
    #Notice how you don’t need to specify a flow_rate attribute to use the defaults（所以blow_out的画风和别人不一样哈）:
    pipette_1chan.pick_up_tip()
    pipette_1chan.aspirate(18, plate_384["A1"])  # 716 µL/s，看simulation里不是35.00µL/s吗？  哦，因为人家教程里用的是1000ul枪头，所以默认的flow rate=716 ul/s
    pipette_1chan.dispense(18, plate_384["A2"])  # 716 µL/s
    pipette_1chan.blow_out()                  # 716 µL/s
    #Now let’s change the flow rates for each action:
    pipette_1chan.flow_rate.aspirate = 50
    pipette_1chan.flow_rate.dispense = 100
    pipette_1chan.flow_rate.blow_out = 300
    pipette_1chan.aspirate(34, plate_384["A2"])  #  50 µL/s
    pipette_1chan.dispense(34, plate_384["A3"])  # 100 µL/s
    pipette_1chan.blow_out()                  # 300 µL/s
    pipette_1chan.drop_tip()
    #These flow rates will remain in effect until you change the flow_rate attribute again or call configure_for_volume(). Calling configure_for_volume() always resets all pipette flow rates to the defaults for the mode that it sets.
    #这也是老知识点了。低容量模式的时候用过。
    pipette_1chan.configure_for_volume(30)

    if not pipette_1chan.has_tip:
        pipette_1chan.pick_up_tip()
    #检查是否已经有枪头，这样可以避免重复拾取枪头。
    pipette_1chan.aspirate(34, plate_384["K14"])
    pipette_1chan.dispense(34, plate_384["L14"])
    
    # 8. Flex pipette flow rates
    #Default flow rates for each pipette-tip combination are the same across all three actions, except where noted.（见Pipette Characteristics网页）
    
    #Additionally:
    #Do not use tips with a higher capacity than the pipette maximum volume.
    #All Flex pipettes have a well bottom clearance of 1 mm for aspirate and dispense actions
    #这两条PCR那一章的老传统了。即加样高度默认是孔上1mm。要设置高度得类似这样：
    pipette_1chan.aspirate(34, plate_384["J14"].bottom(z=2))
    pipette_1chan.dispense(34, plate_384["J15"].top(z=-2))
    pipette_1chan.blow_out() 
    pipette_8chan.drop_tip()

    
    
    
