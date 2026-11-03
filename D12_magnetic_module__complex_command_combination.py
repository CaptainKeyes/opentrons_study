from opentrons import protocol_api

metadata = {
    "protocolName": "D12:Magnetic Block Module加载 & Complex命令的组合",
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

    #所有的模块的耗材必须符合模块的要求，详情见各模块的Supported labware
    plate_buffer = protocol.load_labware("axygen_96_wellplate_500ul","A2")
    #设置一个plate，用来混匀mix

    # 2. Load pipette
    right_pipette = protocol.load_instrument("flex_1channel_50","right",tip_racks=[tips_50]) 
    left_pipette = protocol.load_instrument("flex_1channel_1000","left",tip_racks=[tips_200])

    # 3. Load trash
    trash = protocol.load_trash_bin("A3")
    
    # 4. Load Magnetic Block module
    #The Magnetic Block is an unpowered, 96-well plate that holds labware close to its high-strength neodymium magnets. This module is suitable for many magnetic bead-based protocols, but does not move beads up or down in solution.
    #Because the Magnetic Block is unpowered, neither your robot nor the Opentrons App is aware of this module. You "control" it via protocols to load labware onto the module and use the Opentrons Flex Gripper to move labware on and off the module. 
    #所以Magnetic Block就是个普通磁力架，啥事情也做不了。所以也没啥好说的，就是把plate放上去，拿下来。另外，Magnetic Block是一个96-well plate ，所以别想着什么384板子上磁力架了。
    #啥意思，难道Magnetic module还能做别的事？
    #Magnetic Block的位置固定在D1
    magnetic_block = protocol.load_module(
        module_name="magneticBlockV1", location="D1")
    # Load a 96-well plate on the magnetic block
    mag_plate = magnetic_block.load_labware(
        name="biorad_96_wellplate_200ul_pcr")
    #每次都要注意，opentrons中很多是声明，还是需要分清声明和摆放的差别的
    # create timer for sample incubation
    mag_timer = protocol.create_timer(seconds=90)
    # Let the magnetic block adsorb the beads.
    protocol.wait_for_tasks([mag_timer])
    
    '''
    学会一招新东西，这是这一章里最重要的环境
    '''
    # 5. combine multiple commands into Complex Commands
    #学会一招新的，可以在底层命令中先设置属性，然后高级命令就可以直接沿用底层命令的属性了。
    right_pipette.flow_rate.aspirate = 10
    #right_pipette.aspirate().flow_rate=15
    #flow_rate是个property，aspirate则是有返回值的：InstrumentContext 
    right_pipette.flow_rate.dispense = 30
    source=mag_plate.rows_by_name()["A"]
    dest=plate_buffer.rows_by_name()["A"]
    right_pipette.transfer(20, source, dest, new_tip="always")
    
    # Use the gripper to move labware
    protocol.move_labware(mag_plate, new_location="B2", use_gripper=True)
    
    # 6. Load Magnetic Module
    '''The Magnetic Module is compatible with the OT-2 only. If you have a Flex, use the Magnetic Block.开幕雷击，唉，用不了
    mag_mod = protocol.load_module(
        module_name="magnetic module gen2",location="6")
    plate = mag_mod.load_labware(
        name="nest_96_wellplate_100ul_pcr_full_skirt")
    
    Loading labware¶
    Like with all modules, use the Magnetic Module’s load_labware() method to specify what you will place on the module. The Magnetic Module supports 96-well PCR plates and deep well plates. For the best compatibility, use a labware definition that specifies how far the magnets should move when engaging with the labware. 
    
    Engaging and disengaging¶
    Raise and lower the module's magnets with the engage() and disengage() functions, respectively.

    If your loaded labware is fully compatible with the Magnetic Module, you can call engage() with no argument: 
    mag_mod.engage()
    This will move the magnets upward to the default height for the labware, which should be close to the bottom of the labware's wells. If your loaded labware doesn't specify a default height, this will raise an ExceptionInProtocolError.
    
    For certain applications, you may want to move the magnets to a different height. The recommended way is to use the height_from_base parameter, which represents the distance above the base of the labware (its lowest point, where it rests on the module). Setting height_from_base=0 should move the tops of the magnets level with the base of the labware. 
    Alternatively, you can use the offset parameter, which represents the distance above or below the labware's default position (close to the bottom of its wells). Like using engage() with no argument, this will raise an error if there is no default height for the loaded labware.
    
    Here are some examples of where the magnets will move when using the different parameters in combination with the loaded NEST PCR plate, which specifies a default height of 20 mm:
    mag_mod.engage(height_from_base=13.5)  # 13.5 mm
    基于耗材的物理底部（而不是孔底默认位置）来定位，应该改用 height_from_base 参数。
    mag_mod.engage(offset=-2)              # 15.5 mm
    相对于耗材的默认位置（通常靠近孔底）来微调磁铁高度。
    
    拆解计算过程
    耗材默认高度：NEST PCR 板定义中 default height = 20 mm。这是 engage() 不带参数时磁铁到达的位置。
    offset 的含义：offset 是相对默认高度的偏移量。offset=-2 表示比默认高度低 2 mm，即 20 − 2 = 18 mm。
    Home 位置的修正：GEN2 模块的磁铁原点（home）位置被测量为 −2.5 mm。也就是说，绝对坐标 0 并不是磁铁的最低点，磁铁的 home 在 −2.5 mm 处。
    换算到绝对位置：18 mm（相对默认高度）再减去 home 偏移 2.5 mm，得到 18 − 2.5 = 15.5 mm。
    所以代码注释写的 # 15.5 mm 是换算到模块绝对坐标系后的实际位置，而 offset=-2 是从耗材默认高度出发的相对指令。两者描述的是同一个物理位置，只是参照系不同。
    
    对比 height_from_base
    height_from_base=13.5 则是直接以耗材物理底部为基准给出的绝对高度，不经过默认高度和 home 修正，所以注释就是 13.5 mm。这也是为什么文档建议：想基于耗材底部定位时用 height_from_base，想基于默认高度微调时用 offset。

'''
    
    
    
    
    
    
    
    
    