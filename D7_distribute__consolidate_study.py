from opentrons import protocol_api

metadata = {
    "protocolName": "D7:distribute&Consolidate学习",
    "author": "Your Name"
}#都是字典类型

requirements = {
    "robotType": "Flex",
    "apiLevel": "2.29"
}#都是字典类型


def run(protocol: protocol_api.ProtocolContext):

    # 1. Load labware
    tips_50 = protocol.load_labware(
        "opentrons_flex_96_tiprack_50ul",
        "C2"
    )
    #接下来的体积可能会比较大，为了方便起见，其实可以换枪头，见https://labware.opentrons.com/#/
    tips_200 = protocol.load_labware(
        "opentrons_flex_96_tiprack_200ul",
        "C3"
    )

    plate = protocol.load_labware(
        "corning_96_wellplate_360ul_flat",
        "D2"
    )
    plate_buffer = protocol.load_labware(
        "axygen_96_wellplate_500ul",
        "D1"
    )#设置一个plate，用来混匀mix

    # 2. Load pipette
    right_pipette = protocol.load_instrument(
        "flex_1channel_50",
        "right",
        tip_racks=[tips_50] #列表中的元素名需要对应上labware
        )
    left_pipette = protocol.load_instrument(
        "flex_1channel_1000",
        "left",
        tip_racks=[tips_200] #列表中的元素名需要对应上labware
        )
    #见Tip-pipette compatibility

    # 3. Load trash
    trash = protocol.load_trash_bin(
        "A3"
    )
    
    '''
    # 4. Distrubute()
    #Move a volume of liquid from one source to multiple destinations.
    #用于分装mix。
    right_pipette.distribute(
        100,
        plate_buffer["A1"],
        plate_buffer.rows()[1][:2],  
        )
    #学过的都忘记了，没有plate_buffer[2][:3]这种用法
    #这边看到pipette在自动进行blow_out，并且是blow_out到trash bin中，并不是因为blow_out=True。（其实也能想到，如果说管子里有液体，默认应该是blow_out到source well中，而不是trash bin中）
    #这边执行了45(50)+27.5(32.5)+27.5(32.5)=100ul，括号内为吸取的液体，括号外为实际打到dest中的液体
    right_pipette.distribute(
        120,
        plate_buffer["A2"], #A "single" well to aspirate liquid from.
        plate_buffer.rows()[1][2:4], #A "list" of wells to dispense liquid into.
        blow_out=False #设定为False还是会排空，所以和blow_out没关系
        )
    #45(50)+37.5(42.5)+37.5(42.5)=120ul
    #这是因为distribute 默认执行disposal_volume: Aspirates additional liquid to improve the accuracy of each dispense. Defaults to the minimum volume of the pipette. 
    right_pipette.distribute(
        130,
        plate_buffer["A3"],
        plate_buffer.rows()[1][4:6],
        disposal_volume=0,
        new_tip="always" 
        )
    #50+40+40=130ul
    #如果不排空的话，那就是设置disposal_volume=0，这样就吸多少是多少。
    #mix_after is ignored.这可以理解吧

    # 5. Consolidate()
    #Move liquid from multiple source wells to a single destination well.
    #用于加FR引物到一个孔。    
    right_pipette.consolidate(
        6,
        plate_buffer.rows()[0][3:6], #A "list" of wells to aspirate liquid from.
        plate_buffer["B7"], #A "single" well to dispense liquid into.
        new_tip="always" 
        )
    #这里，new_tip参数也是完成一次consolidate之后才会执行的，同理，之前distribute也是在完成了一次distribute之后才会执行的。所以要记住，在加完一个样品后会接触到底部原有的buffer，不换枪头会造成污染。这里除非悬空加，后续将对这个进行进一步学习。
    #所以可以说，new_tips这个参数在distribute和consolidate中不能说毫无作用吧，只能说作用毫无
    #disposal_volume and mix_before are ignored.这也可以理解吧
    '''
    
    # 6. PCR genotyping
    n=30 #30个样品
    left_pipette.distribute(
        5*n*1.1, #5ul mix
        plate_buffer["C1"],
        plate_buffer.rows()[3][:3], 
        disposal_volume=0 #genotyping不用这么精准
        )
    
    mixs=plate_buffer.rows()[3][:3] #和上面一样，一共三管mix
    for i,mix in enumerate(mixs): #由于是2个引物加1个孔
        '''
        primer=[
            well
            for row in plate_buffer.rows()[2] #就一行，for循环个p
            for well in row[2*i+1:2*i+3]]
        '''
        primer=plate_buffer.rows()[2][2*i+1:2*i+3]
        right_pipette.transfer( #加引物还是不要用consolidate了，不换枪头引物污染了
            0.25*n*1.1, #0.25ul primerF/R
            primer, 
            mix,
            new_tip="always"
            )
        
    left_pipette.transfer(
        3*n*1.1, #3ul H2O
        plate_buffer["C8"],
        plate_buffer.rows()[3][:3], 
        mix_after=(3, 200),
        new_tip="always"
        )
    #由于distribute的mix_after被ban了，所以这里还是只能用transfer
    #另外，原有的50ul，flex_1channel_50和opentrons_flex_96_tiprack_50ul没法对200ul的体积mix，必须换枪头
    
    
    
    
    
    
    