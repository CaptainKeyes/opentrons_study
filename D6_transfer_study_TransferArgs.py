from opentrons import protocol_api

metadata = {
    "protocolName": "D6:transfer的各个参数",
    "author": "Your Name"
}#都是字典类型

requirements = {
    "robotType": "Flex",
    "apiLevel": "2.29"
}#都是字典类型


def run(protocol: protocol_api.ProtocolContext):

    # 1. Load labware
    tips = protocol.load_labware(
        "opentrons_flex_96_tiprack_50ul",
        "C3"
    )

    plate = protocol.load_labware(
        "corning_96_wellplate_360ul_flat",
        "D2"
    )

    # 2. Load pipette
    right_pipette = protocol.load_instrument(
        "flex_1channel_50",
        "right",
        tip_racks=[tips] #列表中的元素名需要对应上labware
        )

    # 3. Load trash
    trash = protocol.load_trash_bin(
        "A3"
    )

    # 4.Transfer():new_tip
    '''
    right_pipette.transfer(
        3.1, 
        plate.rows()[0][:4:2], 
        plate.rows()[1][:4], 
        new_tip="always")
    #Do not pick up or drop tips at all. 
    #所以必须预先加装枪头，而"once", "always"则不能预先装枪头
    right_pipette.pick_up_tip()
    right_pipette.transfer(
        3.2, 
        plate.rows()[0][:4:2], 
        plate.rows()[1][:4], 
        new_tip="never") 
    right_pipette.drop_tip()
    
    right_pipette.transfer(
        3.3, 
        plate.rows()[0][:4:2], 
        plate.rows()[1][:4], 
        new_tip="always",
        trash=False) #python中bool类型就只有True和False，没有T or F
    #If True (default), the pipette will drop tips in its trash_container. If False, the pipette will return tips to their tip rack.
    '''
    right_pipette.transfer(
        3.4, 
        plate.rows()[0][:4:2], 
        plate.rows()[1][:4], 
        new_tip="always",
        touch_tip=True) #如果在transfer中使用touch_tip参数，只能使用默认参数，如果需要自定义，则需要自己编写。
    #If True, perform a touch_tip() following each aspirate() and dispense(). Defaults to False.
    
    # 5.Transfer():touch_tip
    #Touch the pipette tip to the sides of a well, with the intent of removing leftover droplets.
    right_pipette.pick_up_tip() 
    right_pipette.transfer(
        3.5, 
        plate.rows()[0][:4:2], 
        plate.rows()[1][:4], 
        new_tip="never")
    right_pipette.touch_tip(
        location=None, #location=source：在源孔触壁；location=dest：在目标孔触壁
        radius=0.36, #触壁位置距离孔中心约为孔半径的 36%
        v_offset= -2.2, #触壁高度相对于孔顶部向下 2.2 mm
        speed=70.2) #触壁移动速度为 70.2 mm/s
        #mm_from_edge=0.7 吸头距离孔壁边缘 0.7 mm
        #radius 和 mm_from_edge 不能同时设置。两者都是表示How far to move inside the well，只不过一个是百分比，一个是绝对距离
        #真实实验时需要在单孔中进行验证。
    right_pipette.drop_tip()
    
    # 6.Transfer():blow_out
    right_pipette.transfer(
        3.6, 
        plate.rows()[0][:4:2], 
        plate.rows()[1][:4], 
        new_tip="always",
        blow_out=True)
    #If True, a blow_out() will occur following each dispense(), but only if the pipette has no liquid left in it. If False (default), the pipette will not blow out liquid.
    #看模拟就看出来，pipette先打到孔里--移动到trash bin--排空--再移动到trash bin--再打掉枪头。
    
    right_pipette.transfer(
        3.7, 
        plate.rows()[0][:4:2], 
        plate.rows()[1][:4], 
        new_tip="always",
        blow_out=True,
        blowout_location="destination well")
    #Accepts one of three string values: "trash", "source well", or "destination well".
    #这里就解决了上面那个问题，就是排空的液体是排到哪里，这里就是排到dest孔中
    #If blow_out is False (its default), this parameter is ignored.
    #If blow_out is True and this parameter is not set:这里的默认值提供了不同的方式，也就是程序会根据枪头里是否残存液体来判断下一步打到哪里去
        #Blow out into the trash, if the pipette is empty or only contains the disposal volume.
        #Blow out into the source well, if the pipette otherwise contains liquid.
    #为了演示吹回source well的情况
    right_pipette.pick_up_tip()
    right_pipette.aspirate(
        10,
        plate["A1"])
    right_pipette.transfer(
        5,
        plate["B1"],
        plate["C1"],
        new_tip="never",
        blow_out=True )#这里就能看到，剩余液体是默认排空到B1孔中，即blowout_location="source well"
    right_pipette.drop_tip()
    
    # 7.Transfer():mix_before,mix_after
    right_pipette.transfer(
        4.1, 
        plate["A8"], 
        [plate["C8"],plate["C9"]], 
        new_tip="always",
        mix_before=(2, 6.3),
        mix_after=(3, 8))
    # Its value must be a tuple with "two numeric" values. The first value is the number of repetitions, and the second value is the amount of liquid to mix in µL.
    # mix 8 µL of liquid 3 times before/after each of its aspirations/dispenses
    # 在机器中，mix被认为是在well中吸8ul--在well中排液8ul，并推出0ul--再吸--再排，并推的循环
    
    
    
        
        
        
    
