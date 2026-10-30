from opentrons import protocol_api

metadata = {
    "protocolName": "D10:整合整个PCR程序",
    "author": "Your Name"
}#都是字典类型

requirements = {
    "robotType": "Flex",
    "apiLevel": "2.29"
}#都是字典类型


def run(protocol: protocol_api.ProtocolContext):
    # 1. Load labware
    tips_50 = protocol.load_labware("opentrons_flex_96_tiprack_50ul","C2")
    tips_200 = protocol.load_labware("opentrons_flex_96_tiprack_200ul","C3")
    plate_PCR = protocol.load_labware("opentrons_96_wellplate_200ul_pcr_full_skirt","D2")#PCR的板子是特制板子
    plate_buffer = protocol.load_labware("axygen_96_wellplate_500ul","D1")#设置一个plate，用来混匀mix
    plate_sample = protocol.load_labware("corning_96_wellplate_360ul_flat","D3")#设置一个plate，存放样品

    # 2. Load pipette
    pipette_50 = protocol.load_instrument(
        "flex_1channel_50","left",tip_racks=[tips_50])
    pipette_1000 = protocol.load_instrument(
        "flex_1channel_1000","right",tip_racks=[tips_200])
    #见Tip-pipette compatibility

    # 3. Load trash
    trash = protocol.load_trash_bin("A3")
    
    # 4. Load Thermocycler module
    tc_mod = protocol.load_module(module_name="thermocyclerModuleV2")
    
    # 5. Load riser and lids
    riser = protocol.load_adapter(load_name="opentrons_flex_deck_riser",location="A2")
    lid_stack = riser.load_lid_stack(load_name="opentrons_tough_pcr_auto_sealing_lid",quantity=3)
    
    '''
    # 5. Sample prepation
    n=30 #30个样品
    pipette_50.distribute(
        5*n*1.1, #5ul mix
        plate_buffer["C1"],
        plate_buffer.rows()[3][:3], 
        disposal_volume=0)
    
    mixs=plate_buffer.rows()[3][:3] #和上面一样，一共三管mix
    for i,mix in enumerate(mixs): #由于是2个引物加1个孔
        primer=plate_buffer.rows()[2][2*i+1:2*i+3]
        pipette_1000.transfer( #加引物还是不要用consolidate了，不换枪头引物污染了
            0.25*n*1.1, #0.25ul primerF/R
            primer, 
            mix,
            new_tip="always")
        
    pipette_50.transfer(
        3*n*1.1, #3ul H2O
        plate_buffer["C8"],
        plate_buffer.rows()[3][:3], 
        mix_after=(3, 200),
        new_tip="always")
    #由于distribute的mix_after被ban了，所以这里还是只能用transfer
    #另外，原有的50ul，flex_1channel_50和opentrons_flex_96_tiprack_50ul没法对200ul的体积mix，必须换枪头
    '''
    
    
    # ========================================================
    # 6. PCR genotyping
    # ========================================================
    
    # --------------------------------------------------------
    # A. 实验逻辑层：实验参数、试剂体积、孔位布局
    # --------------------------------------------------------
    
    PCR_SAMPLE_COUNT = 30
    PCR_TARGET_NUMBER = 3
    PCR_MIX_VOLUME = 5.0
    PCR_PRIMER_VOLUME = 0.25
    PCR_WATER_VOLUME = 3.0
    PCR_SAMPLE_VOLUME = 1.5
    PCR_EXTRA_FACTOR = 1.1
    
    # 试剂来源孔
    mix_source = plate_buffer["A1"]
    water_source = plate_buffer["A2"]
    
    # 三管预混液，位于 D1、D2、D3
    mix_tubes = plate_buffer.rows()[3][:PCR_TARGET_NUMBER]
    
    # 六个引物来源孔：B1-B6
    # 每两个孔组成一对引物
    primer_wells = plate_buffer.rows()[1][:2 * PCR_TARGET_NUMBER]
    
    # 30 个样品来源孔
    sample_wells = plate_sample.wells()[:PCR_SAMPLE_COUNT]
    
    # 每管 Master Mix 中需要准备的体积
    mix_volume = (
        PCR_SAMPLE_COUNT
        * PCR_MIX_VOLUME
        * PCR_EXTRA_FACTOR
    )
    
    primer_volume = (
        PCR_SAMPLE_COUNT
        * PCR_PRIMER_VOLUME
        * PCR_EXTRA_FACTOR
    )
    
    water_volume = (
        PCR_SAMPLE_COUNT
        * PCR_WATER_VOLUME
        * PCR_EXTRA_FACTOR
    )
    
    # 每个 PCR 孔需要加入的 Master Mix 总体积
    reaction_mix_volume = (
        PCR_MIX_VOLUME
        + 2 * PCR_PRIMER_VOLUME
        + PCR_WATER_VOLUME
    )
    
    # 为每个样品生成 3 个 PCR 反应孔
    def get_sample_destinations(sample_index):
        return [
            plate_PCR.wells()[
                sample_index + group_index * PCR_SAMPLE_COUNT
            ]
            for group_index in range(PCR_TARGET_NUMBER)
        ]  #列表推导式
    
    # 为每管 Master Mix 找到对应的引物对
    def get_primer_pair(group_index):
        start = group_index * 2
        return primer_wells[start:start + 2]
    
    # PCR程序
    PCR_ANNEALING_TEMPRETURE = 55
    PCR_ELONGATING_TIME = 30
    PCR_CYCLE_GRADIENT = 20
    PCR_CYCLE_CONSTANT = 15
    
    # --------------------------------------------------------
    # B. 设备控制层：实际移液操作
    # --------------------------------------------------------
    
    def prepare_master_mix():
        """向三管中分别加入 水、引物、2xMix。"""
        
        # 1. 每管加水
        pipette_1000.distribute(
            water_volume,
            water_source,
            mix_tubes,
            disposal_volume=5
        )
        
        # 2. 每管加入对应的两种引物
        for group_index, mix_tube in enumerate(mix_tubes):
            pipette_50.transfer(
                primer_volume,
                get_primer_pair(group_index),
                mix_tube,
                new_tip="always"
            )
    
        # 3. 2xMix 分装到三管并混匀
        pipette_1000.transfer(
            mix_volume,
            mix_source,
            mix_tubes,
            mix_after=(5, 180),
            disposal_volume=5, #这个参数在transfer中没用
            #transfer() will not aspirate additional liquid if you set disposal_volume. However, it will perform a very small blow out after each dispense.
            new_tip="always"
        )
    
    def add_master_mix_to_pcr_plate():
        """先给所有 PCR 反应孔加入 Master Mix。"""
        '''为了节约枪头，后加Master Mix，且悬空加，不接触样品，加完后贴壁去液滴'''
        
        dispense_well_top = list(plate_sample["A1"].top(z=-1))[0].z 
        #设置加样高度，板子的高度都是一致的，所以随便取个well设个高度即可
        #是列表，怎么之前都知道，真的到写的时候就忘记了
        pipette_50.well_bottom_clearance.dispense = dispense_well_top
        #设置pipette的加样高度，还有，这里是dispense啊
        '''
        # change clearance for dispensing to 14 mm 
        # 还有种方法，一般这种200ul的96孔板，高度大概是14-16mm，因此选一个低于孔高度的
        pipette.well_bottom_clearance.dispense = 14
        '''
        '''
        其实还有个方法，每次调用的时候，设置location的Location参数
        pipette.pick_up_tip()
        well_top = plate["A1"].top(z=-1) #这里是一个well.location参数，也就是每个孔加样的时候都会单独找位置，我嫌麻烦，就直接设置高度。等移液完再将高度调回默认值。
        depth = plate["A1"].bottom(z=2)
        pipette.aspirate(
            volume=200,
            location=well_top,
            end_location=depth
        )
        '''
        
        for group_index, mix_tube in enumerate(mix_tubes):
    
            # 每组 30 个反应孔使用同一管 Master Mix
            start = group_index * PCR_SAMPLE_COUNT
            end = start + PCR_SAMPLE_COUNT
            destination_wells = plate_PCR.wells()[start:end]
    
            # 每组使用一个新枪头；组内只转移相同的 Master Mix；所以为了不污染枪头，设置了要悬空滴加
            pipette_50.pick_up_tip()
    
            for destination in destination_wells:
                pipette_50.aspirate(
                    reaction_mix_volume,
                    #加mix的时候总不能还*1.1吧
                    #自作聪明，本来reaction_mix_volume就是没*extra_factor的
                    mix_tube
                )
                
                pipette_50.dispense(
                    reaction_mix_volume,
                    destination, #即，此处可以设置destination.top(z=-1)
                )
                
                #这里怎么贴壁加啊，好像没法贴壁加，只能加了再贴壁
                #这里blow_out好像也没意义，你不贴壁，blow_out出来后，mix的液体也打不进孔里
    
                # 先打液，再触壁
                pipette_50.touch_tip(
                    location=destination, 
                    radius=1.0,
                    v_offset=-2,
                    speed=20
                )
                
    
            pipette_50.drop_tip()
        
        pipette_50.well_bottom_clearance.dispense =  1 
        #复位回1mm
    
    def add_samples_to_pcr_plate():
        """每个样品分到对应的三个 PCR 反应孔。"""
        '''为了节约枪头，先加sample，且贴底加，保证加到孔中，加完后不贴壁'''
    
        # Flex 50 µL 移液器切换到低体积模式
        pipette_50.configure_for_volume(PCR_SAMPLE_VOLUME)
    
        for sample_index, sample_well in enumerate(sample_wells):
            destinations = get_sample_destinations(sample_index)
    
            # 一个样品使用一个新枪头，分到对应的三个反应孔
            pipette_50.distribute(
                PCR_SAMPLE_VOLUME,
                sample_well,
                destinations,
                disposal_volume=2.0
            )
            #一般程序默认是加样的时候是在底部
            #If you specify a single location like the well "A1", the pipette will aspirate from a default position 1 mm above the bottom center of that well. To change the default clearance, first set the aspirate attribute of well_bottom_clearance
            
            '''
            如果先加mix，再加sample，记得把sample加在液面下（虽然默认都是孔底上1mm，但是加在液面下可以减少mix损失
            pipette_50.distribute(
                PCR_SAMPLE_VOLUME,
                sample_well,
                location=destinations.meniscus(z=-1, target="start"),
                end_location=destinations.meniscus(z=-1, target="end"),
                disposal_volume=2.0
            )
            '''
        
        #把低体积模式给关掉
        pipette_50.configure_for_volume(10) 
    
    def move_placte_to_pcr_module():
        tc_mod.open_lid()
        
        protocol.move_labware(
            labware=plate_PCR, 
            new_location=tc_mod,
            use_gripper=True
            )
        
        # move lid to PCR plate
        protocol.move_lid(
            source_location=lid_stack,
            new_location=plate_PCR,
            use_gripper=True
            )
        
        tc_mod.close_lid()
        
    def pcr_program():
        tc_mod.set_lid_temperature(temperature=100)

        for i in range(PCR_CYCLE_GRADIENT):
            profile_cycle_greadient = [
                {"temperature":95, "hold_time_seconds":30},
                {"temperature":65-i*0.5, "hold_time_seconds":30},
                {"temperature":72, "hold_time_seconds":PCR_ELONGATING_TIME}]
            tc_mod.execute_profile(
                steps=profile_cycle_greadient, 
                repetitions=1,  #repetitions参数不可省
                block_max_volume=12)
        
        profile_cycle_constant = [
            {"temperature":95, "hold_time_seconds":30},
            {"temperature":PCR_ANNEALING_TEMPRETURE, "hold_time_seconds":30},
            {"temperature":72, "hold_time_seconds":PCR_ELONGATING_TIME}]
        tc_mod.execute_profile(
            steps=profile_cycle_constant, 
            repetitions=PCR_CYCLE_CONSTANT,  #repetitions参数不可省
            block_max_volume=12)
        
        tc_mod.start_set_block_temperature(temperature=10) #本来保温和热盖液没什么关系，可以不用等保温到10度再关热盖
        tc_mod.deactivate_lid()

            
    
    # --------------------------------------------------------
    # C. 主流程：按实验顺序调用控制函数
    # --------------------------------------------------------
    
    prepare_master_mix()
    add_samples_to_pcr_plate()
    add_master_mix_to_pcr_plate()
    move_placte_to_pcr_module()
    pcr_program()
            
        
            
        
    