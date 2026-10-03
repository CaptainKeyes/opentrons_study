from opentrons import protocol_api

metadata = {
    "protocol_name": "D0：opentrons新手教程，基本移液操作",
    "producer": "Your Name"
}#都是字典类型

requirements = {
    "robotType": "Flex",
    "apiLevel": "2.29"
}#都是字典类型


def run(protocol: protocol_api.ProtocolContext):

    # 1. Load labware
    tipsss = protocol.load_labware(
        "opentrons_flex_96_tiprack_50ul",
        "C3"
    )

    platesss = protocol.load_labware(
        "corning_96_wellplate_360ul_flat",
        "D2"
    )

    # 2. Load pipette
    pipettesss = protocol.load_instrument(
        "flex_1channel_50",
        "right", #left移液器和right移液器都行
        tip_racks=[tipsss] #列表中的元素名需要对应上labware
    )

    # 3. Load trash
    trashsss = protocol.load_trash_bin(
        "A3"
        )
    
    # 4. Pick up tip
    pipettesss.pick_up_tip()
    #从C3板位的Opentrons Flex 96 Tip Rack 50 µL的A1孔中拾取吸头

    # 5. Transfer 20 µL
    pipettesss.aspirate(
        20,
        platesss["A1"] #需要对应上labware
    )
    #从D2板位的Corning 96 Well Plate 360 µL Flat的A1孔中以35.00µL/s的速度吸液20.00µL

    pipettesss.dispense(
        20,
        platesss["B1"]
    )
    #以57.00µL/s的速度将20.00µL 排液至D2板位的Corning 96 Well Plate 360 µL Flat的B1孔中
    # 6. Drop tip
    pipettesss.drop_tip()  #既然有droptip就需要设置trash_bin
    #移动到垃圾桶在A3
    #将吸头丢入垃圾桶在A3

    #同样，从A1吸50ul到B1
    pipettesss.pick_up_tip()  #既然打掉了枪头，肯定要给个枪头
    pipettesss.aspirate(50,platesss["A1"])
    pipettesss.dispense(50,platesss["B1"])
    pipettesss.drop_tip() 