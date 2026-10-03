from opentrons import protocol_api

metadata = {
    "protocolName": "D1：for range循环对groups of wells移液",
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
    
    # 4. Pick up tip
    right_pipette.pick_up_tip()
    #从C3板位的Opentrons Flex 96 Tip Rack 50 µL的A1孔中拾取吸头

    # 5. Accessing wells in labware
    #从A1 → B1、A2 → B2、A3 → B3 
    for i in range(3): #range是左闭右开
        source = plate.rows()[0][i]
        #记住，plate要和上面的plate相对应
        #这边学会一个重要参数，plate.rows，即按行进行[行][列]
        #rows():List of lists grouped by row.[[labware:A1, labware:A2...], [labware:B1, labware:B2...]]
        destination = plate.rows()[1][i]
        right_pipette.aspirate(20, source)
        right_pipette.dispense(20, destination)
    #从C1 → D1、C3 → D3 
    for i in range(0,4,2): #遵循range的语法，list(range(0,4,2))
        source = plate.rows()[2][i]
        destination = plate.rows()[3][i]
        right_pipette.aspirate(30,source)
        right_pipette.dispense(30,destination)
    #行和列一定要搞搞清楚。
    #从C3 → C4、D3 → D4、E3 → E4 
    for i in range(2,5):
        source = plate.columns()[2][i]
        destination = plate.columns()[3][i]
        right_pipette.aspirate(30,source)
        right_pipette.dispense(30,destination)
        #同理，plate.columns()，按列进行[列][行]
        #columns():List of lists grouped by column.[[labware:A1, labware:B1...], [labware:A2, labware:B2...]]
    #从A1 → A2、B1 → B2 
    for i in range(9):
        source = plate.wells()[i]
        destination = plate.wells()[i+8]
        right_pipette.aspirate(30,source)
        right_pipette.dispense(30,destination)
        #plate.wells():List of all wells.[labware:A1, labware:B1, labware:C1...]
 
    # 6. Drop tip
    right_pipette.drop_tip()  #既然有droptip就需要设置trash_bin
    #移动到垃圾桶在A3
    #将吸头丢入垃圾桶在A3
