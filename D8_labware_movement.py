from opentrons import protocol_api

metadata = {
    "protocolName": "D8:Labware移动",
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

    #plate = protocol.load_labware("corning_96_wellplate_360ul_flat","D2")
    #Corning 板（360ul flat）：绝对不能放入Thermocycler模块。它没有全裙边，热循环模块的自动开盖/关盖机械结构无法抓取它；而且平底设计导致它无法与加热模块紧密贴合，升降温效率极差。
    plate = protocol.load_labware("opentrons_96_wellplate_200ul_pcr_full_skirt","D2")
    #所有的模块的耗材必须符合模块的要求，详情见各模块的Supported labware
    plate_buffer = protocol.load_labware("axygen_96_wellplate_500ul","D1")
    #设置一个plate，用来混匀mix

    # 2. Load pipette
    right_pipette = protocol.load_instrument("flex_1channel_50","right",tip_racks=[tips_50]) 
    left_pipette = protocol.load_instrument("flex_1channel_1000","left",tip_racks=[tips_200])

    # 3. Load trash
    trash = protocol.load_trash_bin("A3")
    
    # 4. Load module
    #Use the load_labware() method on the module context to load labware on a module. 
    #加载module
    tc_mod = protocol.load_module(
        module_name="thermocyclerModuleV2")
    #module_name (str) – The name or model of the module. See Available Modules for possible values. 
    #location (DeckLocation | None, default: None ) – The location of the module.
    #This is usually the name or number of the slot on the deck where you will be placing the module, like 1, "1", or "D1". See Deck Slots.
    #The Thermocycler is only valid in one deck location. You don't have to specify a location when loading it, but if you do, it must be 7, "7", or "B1". See Thermocycler Module.
    #这就是官网教程里为什么没有指定位置。
    #Changed in version 2.15: You can now specify a deck slot as a coordinate, like "D1".
    #加载module对应的labware
    #这是说明Labware就是在module上
    tc_plate = tc_mod.load_labware( 
        name="opentrons_96_wellplate_200ul_pcr_full_skirt",
        label="Temperature-Controlled Tubes")#顾名思义，label这个参数可有可无
    #When you load labware on a module, you don’t need to specify the deck slot. In the above example, the load_module() method already specifies where the module is on the deck: location="D1".
    #见Moving Labware章节：Supported labware
    
    # 5. Basic movement 
    #Move a loaded labware to a new location.
    #Use the ProtocolContext.move_labware() method to initiate a move, regardless of whether it uses the gripper.
    protocol.move_labware(labware=plate, new_location="B3")
    #The required arguments of move_labware() are the labware you want to move and its new_location. You don't need to specify where the move begins, since that information is already stored in the Labware object—plate in this example. 
    #The destination of the move can be any empty deck slot, or a module that's ready to have labware added to it (see Movement with Modules below). 
    
    #When the move step is complete, the API updates the labware's location, so you can move the plate multiple times:
    protocol.move_labware(labware=tips_200, new_location="C1")
    protocol.move_labware(labware=tips_200, new_location="C3")
    
    # 6. Automatic vs manual moves
    #There are two ways to move labware:
        #Automatically, with the Opentrons Flex Gripper.
        #Manually, by pausing the protocol until a user confirms that they've moved the labware.
    #The use_gripper parameter of move_labware() determines whether a movement is automatic or manual. Set its value to True for an automatic move. 
    #The default value is False, so if you don't specify a value, the protocol will pause for a manual move. （所以你在opentrons模拟器里能看到手动将……移动至……）
    # have the gripper move the plate from B3 to B2 (line 57)  （这里在opentrons模拟器中可以看到使用转板抓手将……）
    protocol.move_labware(labware=plate, new_location="B2", use_gripper=True)
    # pause to move the plate manually from B2 to B3
    protocol.move_labware(labware=plate, new_location="B3", use_gripper=False)
    # pause to move the plate manually from B3 to D2 (gripper default is False)
    protocol.move_labware(labware=plate, new_location="D2")
    # You don't have to load the gripper as an instrument, and there is no InstrumentContext for the gripper. All you have to do to specify that a protocol requires the gripper is to include at least one move_labware() command with use_gripper=True.  总之，gripper不是一个单独的instrument。
    
    '''
    7. Supported labware
    The labware definitions listed above include information about the position and force that the gripper uses to pick up the labware. The gripper uses default values for labware definitions that don't include position and force information. The Python Protocol API won't raise a warning or error if you try to grip and move other types of labware.
    这里需要注意的是，其实理论上所有的Labware都可以手动移动，但是当使用gripper机械臂的时候就只有Supported labware列表中的才行。
    当然理论上非标Labware也可以，但是gripper会抓不住。（如没有边缘什么的，会导致抓取过程中打翻，即使你用gripper去抓非标耗材人家也不会报错
    
    8. Movement with modules
    Moving labware on and off of modules lets you precisely control when the labware is in contact with the hot, cold, or magnetic surfaces of the modules.
    When moving labware anywhere that isn't an empty deck slot, consider what physical object the labware will rest on following the move. That object should be the value of new_location, and you need to make sure it's already loaded before the move. 
    For example, if you want to move a 96-well flat plate onto a Heater-Shaker module, you actually want to have it rest on top of the Heater-Shaker's 96 Flat Bottom Adapter. Pass the adapter, not the module or the slot, as the value of new_location:
     # 1. 在 D1 位置放一个普通的板子（准备被移动）
    plate = protocol.load_labware("nest_96_wellplate_200ul_flat", "D1")
    # 2. 在 C1 位置加载加热振荡器模块
    hs_mod = protocol.load_module("heaterShakerModuleV1", "C1")
    # 3. 在模块上加载一个适配器，命名为 hs_adapter
    hs_adapter = hs_mod.load_adapter("opentrons_96_flat_bottom_adapter")
    # 4. 【关键】打开加热振荡器的夹具，腾出物理空间
    hs_mod.open_labware_latch()
    # 5. 【关键】用机械臂把 D1 的板子，移到 C1 的适配器上
    protocol.move_labware(
        labware=plate, new_location=hs_adapter, use_gripper=True
        # 注意这里是 adapter，不是 C1，也不是 hs_mod
    )
    在 Opentrons 的甲板上，模块上面不一定能直接放板子。很多时候，模块上面需要先放一个适配器（Adapter），板子再放在适配器上。
    你在 C1 位置放了一个加热振荡器（hs_mod）。
    加热振荡器上面放了一个平底适配器（hs_adapter）。
    你要移动的板子（plate）最终是要落在适配器上的。
    所以在写 protocol.move_labware() 时，new_location 不能填 "C1"，也不能填 hs_mod，必须填适配器 hs_adapter。因为适配器是这个物理堆叠（Slot -> Module -> Adapter）里最顶层、真正空着等待承接板子的地方。如果你填了 C1 或模块本身，系统会报错（因为位置被占了）。
    '''
    #引号注释也得保证缩进啊！！！
    
    # 9. Moving lids
    #You can use ProtocolContext.move_lid() to move labware lids around the deck manually or using the Flex Gripper. 
    #Currently supported lids include the Opentrons Tough Universal Lid, the Opentrons Tough PCR Auto-Sealing Lid (for use with the Thermocycler), and the Opentrons Flex Tip Rack Lid.
    #You can move the auto-sealing lids between deck slots, lid stacks, or compatible labware loaded in your protocol. 
    #line34:load Thermocycler and plate
    # load lid stack
    lid_stack = protocol.load_lid_stack(
        load_name="opentrons_tough_pcr_auto_sealing_lid",  #翻字典Labware Library
        location="A2",
        quantity=4  #The quantity of lids to be loaded in the stack.
        )
    # move one lid to a compatible well plate in the Thermocycler
    tc_mod.open_lid()
    protocol.move_lid(
        source_location=lid_stack, #注意这里是source_location
        new_location=tc_plate,
        use_gripper=True
        )
    #When you're done with a lid, use move_lid() to dispose of it in the waste chute or a trash bin:
    #注意，这个拿走盖子是真的拿走盖子，"opentrons_tough_pcr_auto_sealing_lid"本身不会像qPCR膜那个样子粘在PCR板子上。所以并不是像qPCR膜一样把膜撕掉。
    #这个耗材的材质是聚砜（Polysulfone），它是一个有刚性边框的盖子，中间有密封结构。它的密封原理是：当热循环仪的加热盖压下来时，把盖子紧紧压在 PCR 板孔的上方，形成物理密封来防止蒸发和污染。它不是靠粘合剂贴在板子上的，所以 PCR 结束后，机械臂抓住边框把它拿起来时，它就会整个脱离，不会在板子上留下残胶。
    #等等，那我只要做一个大的托盘，里面放上类似于罗氏qPCR膜这样的静电膜是否就可以了呢，然后压下去的时候可以自动吸附上孔板，相比普通的lid可以降低液面蒸发    
    protocol.move_lid(
        source_location=tc_plate,
        new_location=trash,
        use_gripper=True
        )
    #唯一需要你提前确认的事：橡胶密封垫
    #在盖这个一次性盖子之前，必须确认你的 Thermocycler 盖子上没有安装可重复使用的橡胶密封垫（Rubber Automation Seal）。 官方明确警告：一次性盖子不能和橡胶垫同时使用，否则热循环仪盖子关不严，会导致温度控制异常甚至机械损坏。如果你的机器上装着那个橡胶垫，需要先把它拆下来。
    #To work with tip rack lids, first load the tip rack lid using the lid parameter of load_labware(). 这就是后话了，可以后面再学。 包括pick_up_offset 和drop_offset 是放lid的坐标，这个也是后面再学。   

    #10. Movement into the waste chute
    #Move used tip racks and well plates to the waste chute to dispose of them. This requires you to first configure the waste chute in your protocol. Then use the loaded WasteChute object as the value of new_location: 
    chute = protocol.load_waste_chute()
    #The load_waste_chute() method takes no arguments, since D3 is the only valid location for the chute. However, there are multiple variant configurations of the waste chute, depending on how other methods in your protocol use it.
    protocol.move_labware(
        labware=tc_plate, new_location=chute, use_gripper=True
        )
    #Always specify use_gripper=True when moving labware into the waste chute. The chute is not designed for manual movement. You can still manually move labware to other locations, including off-deck, with the chute installed.
    '''
    这样做是不行的
    protocol.move_labware(
        labware=tc_plate,  
        new_location=trash,
        use_gripper=True
        )
    Can only dispose of tips and Lid-type Labware in a Trash Bin. Did you mean to use a Waste Chute?
    
    再强调一下，必须放D3，这是固定卡槽
    '''

    #module中的板子已经被扔到chute了，放进已经加好mix的板子
    protocol.move_labware(
        labware=plate,  #注意这里是labware
        new_location=tc_mod,
        use_gripper=True
        )
    protocol.move_lid(   #move_lid和move_labware是两个操作
        source_location=lid_stack, #注意这里是source_location
        new_location=plate,
        use_gripper=True
        )
    tc_mod.close_lid()
    
  
    
