from opentrons import protocol_api

metadata = {
    "protocolName": "D5:transfer映射思维练习",
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

    # 4.Transfer exercise
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
        
    #sample:A2,A3,A4,A5,A6
    #gene:A1,B1,C1,D1,E1,F1,G1
    #sample:B2-B3*5 column
    #gene:B2*7 row
    sources = [] #在用append之前得先定义sources
    for i in plate.rows()[0][1:6]:
        sources.append(i)
        # i=0 → A1
        # i=1 → A2
        # i=2 → A3
    '''
    for row in plate.rows()[2:4]:
        well=plate.
        dest.append(plate.columns()[2*i-1:2*i+1])
        这里i是哪里来的呢，而且这里的i也不是数字啊（是plate.rows()[0][1:3]啊，纯扯淡了
    '''
    dests = []
    for column in plate.columns()[1:11]: #这边有个小技巧，就是右边区间就是终止坐标，左边区间是起始坐标+1。例如想从B2加到F2，起始就是2-1（B），终止就是6（F）
        well=column[1:8] #从B2到H2
        dests.append(well)
        #这种方式有个不好的地方，就是两个复孔不是一起点的，会造成差异
        #为了两个复孔能一起点，就需要按行来算
    right_pipette.transfer(volume= 4.4,source= sources,dest=dests,)
    
    '''
    example:
    for i in range(3):
        source = plate.columns()[1][i]  
        # i=0 → A2
        # i=1 → B2
        # i=2 → C2
        dest = []
        for row in plate.rows()[:6]: 先写通用的那一段(此处是1-6行都需要加)
            for well in row[i*3+3:i*3+6]:  再写有i的那一段（此处是对每一行加i*3+3:i*3+5列
                dest.append(well)
        right_pipette.transfer(volume= 5.8,source= source,dest= dest)
        #注意，这里的思想是一个循环完成一次transfer，而不是所有样品放在一起做一次transfer。用这个思想在做一次
     '''
    #sample:A2,A3,A4,A5,A6
    for i in range(1,6):
        source=plate.rows()[0][i]
        dest=[]
        for column in plate.columns()[i*2-1:i*2+1]: #最高到不了6的呀，最高到5呀
            for well in column[1:7]:
                dest.append(well)
        right_pipette.transfer(volume= 3.6,source= source,dest= dest)
        #注意，这里的思想是一个循环完成一次transfer，而不是所有样品放在一起做一次transfer。用这个思想在做一次
    
    #gene:A1,B1,C1,D1,E1,F1
    for i in range(6):
        source=plate.columns()[0][i]
        dest=[]
        for column in plate.columns()[1:11]:
            for well in column[i+1:i+2]:  #这是列表，用的是[]，不是()；另外，列表是一个区间，不能说column[i+1]就结束了
                dest.append(well)
        right_pipette.transfer(volume=6.6, source=source, dest=dest)
    
    #sample:A2,A3,A4,A5,A6
    sources = plate.rows()[0][1:6]
    for i,source in enumerate(sources):
        dest=[
            well
            for row in plate.rows()[1:7]
            for well in row[2*i+1:2*i+3]
            ]
        right_pipette.transfer(
            4.3,
            source,
            dest
        )
    #gene:A1,B1,C1,D1,E1,F1
    sources=plate.columns()[0][:6]    
    for i in range(6):
        dest=[]
        for column in plate.columns()[1:11]:
            for well in column[i+1:i+2]:  #这是列表，用的是[]，不是()；另外，列表是一个区间，不能说column[i+1]就结束了
                dest.append(well)
        right_pipette.transfer(volume=6.6, source=source, dest=dest)
        
    sources=plate.columns()[0][:6]
    for i,source in enumerate(sources):
        dest=[
            well
            for row in plate.rows()[i+1:i+2] #同样的问题，这是列表，需要有头有尾，不能只有一个就结束了
            for well in row[1:11]
            ]
        right_pipette.transfer(
            5.7,
            source,
            dest
        )
        
        
    
    
    
        
        
        
    