from opentrons import protocol_api

metadata = {
    "protocolName": "D4:transfer映射思维学习",
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
    
    # 4. Transfer
    #Move liquid from one well or group of wells to another.
    #Transfer is a higher-level command, incorporating other InstrumentContext commands, like aspirate() and dispense(). It makes writing a protocol easier at the cost of specificity. 
    #transfer有三个主要的参数，这个你直接打pipette.transfer()，IDLE会自己跳出来
    #volume (float | Sequence[float]) – The amount, in µL, to aspirate from each source and dispense to each destination. If volume is a list（这点需要注意，就是说可以一对多加样）, each amount will be used for the source and destination at the matching index.（说明我可以吸40，打20。这在打少量液体样品上非常重要，如吸1ul打1ul样品，很难保证精准，则吸5ul，打1ul，剩余4ul，这样会好很多） A list item of 0 will skip the corresponding wells entirely.
    #source (AdvancedLiquidHandling) – A single well or a list of wells to aspirate liquid from.
    #dest (AdvancedLiquidHandling) – A single well or a list of wells to dispense liquid into.
    #qPCR加样实例：
    #学会mapping（样品-孔位映射） 思维。
    
    #第一列都是cDNA
    #第二列都是SYBR GREEN gene mix
    #想要将A1 加到A4-A12，B2 加到B4-B12以此类推，F1加到F4-F12孔中
    for i in range(6):
        right_pipette.transfer(
            volume=4,
            source=plate.columns()[0][i], #第一个样品
            dest=plate.rows()[i][3:12],  #3个复孔，3个基因，9个孔
            )
    
    #然后将A2 加到A4-F6，A3加到A7-F9，A4加到A10-F12
    '''
    for i in range(3):
        right_pipette.transfer(
            volume=6,
            source=plate.columns()[1][i], #第一个样品
            dest=plate.rows()[:6][i*3+4:i*3+7],  #456  789  101112
            )
    '''
    #这样做是不对的，因为是先得到plate.rows()[:6]这A-F一整行的切片，无法对其中的列进行操作。   
    #--------------重要------------------
    for i in range(3):
        source = plate.rows()[0][i+1]  
        # i=0 → A2
        # i=1 → A3
        # i=2 → A4
        dest = []
        for row in plate.rows()[:6]:
            for well in row[i*3+3:i*3+6]:
                dest.append(well)
        right_pipette.transfer(
            volume=6,
            source=source,
            dest=dest
        )
    '''
    dest = []
    for row in plate.rows()[:6]:
        for well in row[3:6]:
            dest.append(well)
    #可缩写成下式。
    #这里有个重要的知识点：List Comprehension（列表推导式）。它是 Python 创建列表的一种简洁写法。
    dest = [
        well
        for row in plate.rows()[:6]
        for well in row[i*3+3:i*3+6]
    ]
    第一步：
    先看plate.rows()[:6]：A-F行
    第二步：
    外层循环
    for row in plate.rows()[:6]
    第一次，生成plate.rows()[0]的列表row=[A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 A11 A12]，
    第三步：
    内层循环
    执行for well in row[i*3+3:i*3+6]，若i=0，则生成
    well=row[3:6]即[A4 A5 A6]
    相比普通写法，列表推导式更接近数学表达，更加简洁。
    '''
    #是不是等价于下面这样写？
    #同样的问题！！！！！不等价与下面的书写。注意循环和分片的操作差别！！
    '''
    right_pipette.transfer(
        volume=6,
        source=plate.columns()[0][:5], #5个孔
        dest=plate.rows()[:5][3:12],  #5*9个孔
    )
    plate.rows()[:3]是一个“3”个元素的列表，每个元素中有“12”个元素，不能把它认为是一个R语言的矩阵来应对。
    [[A1 of Corning 96 Well Plate 360 µL Flat on slot 2,
      A2 of Corning 96 Well Plate 360 µL Flat on slot 2,
      ……
      A12 of Corning 96 Well Plate 360 µL Flat on slot 2],
     [B1 of Corning 96 Well Plate 360 µL Flat on slot 2,
      B2 of Corning 96 Well Plate 360 µL Flat on slot 2,
      ……
      B12 of Corning 96 Well Plate 360 µL Flat on slot 2],
     [C1 of Corning 96 Well Plate 360 µL Flat on slot 2,
      C2 of Corning 96 Well Plate 360 µL Flat on slot 2,
      ……
      C12 of Corning 96 Well Plate 360 µL Flat on slot 2]]
    plate.rows()[:3][1:2]这里就能看出来，取第1个列表的[1:2]其实就是取了外层列表的第2个元素，即是一个简单的分片操作
    [[B1 of Corning 96 Well Plate 360 µL Flat on slot 2,
      B2 of Corning 96 Well Plate 360 µL Flat on slot 2,
      ……
      B12 of Corning 96 Well Plate 360 µL Flat on slot 2]]
    '''
    #这里可以把source也用row_name变量替换掉
    sources = [
        plate["A2"],
        plate["A3"],
        plate["A4"]
        ]
    for i, source in enumerate(sources):
        dest = [
            well
            for row in plate.rows()[:6]
            for well in row[i*3+3:i*3+6]
        ]
        right_pipette.transfer(
            6,
            source,
            dest
        )
    '''
    这就是自动化液体处理里很典型的 mapping（样品-孔位映射） 思维。
    source列表
     +
    循环索引 i
     +
    自动生成dest区域
    该思路有助于简化思考，不需要去计算source和dest的整除关系，并且增加可读性，总之好处多多，需要多加练习。
    '''
    
    '''
    enumerate是 Python 中非常常用的带索引遍历列表的写法。
    你可以把它拆成两个部分理解：
    * enumerate()
    * for i, source in ...
    
    1. 先看普通的 for 循环
    for source in sources:print(source)
    A2
    A3
    A4
    但是你不知道当前是第几个。
    
    2. 如果你还想知道编号
    for i in range(len(sources)):
        source = sources[i]
        print(i, source)
    0 A2
    1 A3
    2 A4
    这样能看到索引了
    
    3. enumerate()就是把这一步简化
    for i, source in enumerate(sources):
    等价于
    for i in range(len(sources)):
        source = sources[i]
    也就是说python会自动帮你生成
    (i, source) 元组，其中i就是索引，source就是当前索引的元素
    
    例如：
    sources = ["A2", "A3", "A4"]
    for i, source in enumerate(sources):
        print(i, source)
    0 A2
    1 A3
    2 A4
    
    4. 放回原场景
    for i, source in enumerate(sources):
    第一次循环时候
    即一次性生成i=0,source=plate["A2"]
    
    即，学 rows()/columns() 是理解板的位置，enumerate() 是理解如何批量控制这些位置。
    '''

    


    


