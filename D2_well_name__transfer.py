from opentrons import protocol_api

metadata = {
    "protocolName": "D2:自然语言坐标&transfer初探",
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

    # 5.Dictionary access：用自然语言来描述格子坐标
    #The simplest way to refer to a single well is by its well_name, like A1 or D6. Referencing a particular key in the result of Labware.wells_by_name() accomplishes this. 
    #Whichever well access method you use, your protocol will be most maintainable if you use only one access method consistently.
    a1 = plate.wells_by_name()["A1"] #注意索引方式，是plate.wells_by_name()作为一个大列表，在索引其中的["A1"]
    d6 = plate["D6"]  # dictionary indexing这种方法更简便
    right_pipette.aspirate(20, a1)
    right_pipette.dispense(20, d6)
    
    right_pipette.aspirate(20, plate["E5"])
    right_pipette.dispense(20, plate["E7"])
    #When handling liquid, you can provide a group of wells as the source or destination. 
    #该用法和上一章的rows()column()坐标索引是一样的，可以更方便理解和阅读
    row_dict = plate.rows_by_name()["A"]
    row_list = plate.rows()[0]  # equivalent to the line above
    column_dict = plate.columns_by_name()["1"]
    column_list = plate.columns()[0]  # equivalent to the line above
    row_dictB = plate.rows_by_name()["B"]
    #而如果要对一排液体进行移液，"flex_1channel_50"是不行的，需要用"flex_8channel_1000"进行操作，因为本质是对一个列表（见下文）
    #right_pipette.aspirate(20, row_dict)错误的
    #right_pipette.aspirate(20, row_dictB)
    #Since these methods return either lists or dictionaries, you can iterate through them as you would regular Python data structures.
    #For example, to transfer 50 µL of liquid from the first well of a reservoir to each of the wells of row "A" on a plate:
    
    reservoir = protocol.load_labware(
        "nest_12_reservoir_15ml", 
        "D1"
    )
    # 6. Drop tip
    right_pipette.drop_tip()  #既然有droptip就需要设置trash_bin
    #移动到垃圾桶在A3
    #将吸头丢入垃圾桶在A3
    
    # 7. transfer()
    #问题是：transfer() 默认会自己管理枪头,transfer() 默认相当于：自己 pick_up_tip()，aspirate()，dispense()，drop_tip()。因此，此时再用transfer()就会报"have a tip attached"的错。
    for well in plate.rows()[0]:
        right_pipette.transfer(50,reservoir["A1"], well)
    #Equivalently, using rows_by_name:
    for well in plate.rows_by_name()["A"]:
        right_pipette.transfer(50,reservoir["A1"], well)
    #因此，有两种方法，1：将transfer()用在drop_tip()之后。
 


'''
#如果想直接在Spyder 里面自己观察这些东西，用get_protocol_api()即可
from opentrons.simulate import get_protocol_api
protocol = get_protocol_api("2.20")
plate = protocol.load_labware(
    "corning_96_wellplate_360ul_flat",
    "D2"
)
print(plate["A1"])

row_dict = plate.rows_by_name()["A"]
print(row_dict)
#这里故意没有写def run(protocol)。因为现在我们的目的不是写一个完整 protocol，而是：在 Spyder 里创建一个假的 protocol，然后直接研究 plate 到底是什么。
'''