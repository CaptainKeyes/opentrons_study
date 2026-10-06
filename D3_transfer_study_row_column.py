from opentrons import protocol_api

metadata = {
    "protocolName": "D3:transfer列表变量与移液次数",
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
    #Example orders:
    #The smallest possible number of steps in a complex command like transfer() is just two: aspirating and dispensing. This is possible by omitting the tip pickup and drop steps:
    right_pipette.pick_up_tip()
    right_pipette.transfer(
        volume=20,
        source=plate["A1"],
        dest=plate["B1"],
        new_tip="never",
    )
    right_pipette.drop_tip()
    #You can also use new_tip="never" to reuse pipette tips and decrease the total number of steps in any liquid class complex command.
    
    #Tip refilling:
    #One factor that affects the exact order of steps for a complex command is whether the amount of liquid being moved can fit in the tip at once. If it won't fit, you don't have to adjust your command. The API will handle it for you by including additional steps to refill the tip when needed.
    #For example, say you need to move 100 µL of liquid from one well to another, but you only have a 50 µL pipette attached to your robot. To accomplish this with building block commands, you'd need multiple aspirates and dispenses. aspirate(volume=100) would raise an error, since it exceeds the tip's volume. But you can accomplish this with a single command:
    right_pipette.pick_up_tip()
    right_pipette.transfer(
        volume=100, #需要移液的体积
        source=plate["A1"],
        dest=plate["B1"],
        new_tip="never",
    )
    right_pipette.drop_tip()
    
    right_pipette.pick_up_tip()
    right_pipette.transfer(
        volume=75,
        source=plate["A1"],
        dest=plate["B1"],
        new_tip="never",
    )
    right_pipette.drop_tip()
    
    #List of volumes:
    #Legacy complex commands like transfer() can aspirate or dispense different amounts for different wells, rather than the same amount across all wells.
    #To do this in a transfer(), set the volume parameter to a list of volumes instead of a single number. The list must be the same length as the number of source or dest (or the longer of the two for a transfer()), or the API will raise an error（这里也说明了，这里必须要用list变量，做qPCR可以用列表）. For example, this command transfers a different amount of liquid into each of wells B1, B2, and B3:
    right_pipette.transfer(
        volume=[20, 40, 60],#这里60ul，transfer程序会自动分30ul吸两次
        source=plate["A1"],
        dest=[plate["B1"], plate["B2"], plate["B3"]],
        )
    #Setting any item in the list to 0 will skip aspirating and dispensing for the corresponding well. This example takes the command from above and skips B2:
    right_pipette.transfer(
        volume=[20, 0, 60],
        source=plate["A1"],
        dest=[plate["B1"], plate["B2"], plate["B3"]],
        )
    
    #如果我设置不同的source呢？
    #是可以的，而且它会把较短的列表“扩展”到较长列表的长度。官方文档明确说明，transfer() 可以有不同数量的 source 和 destination；较长列表的长度决定 transfer 次数，并要求长列表长度能被短列表长度整除。也就是短的 source 列表会被“重复使用”。
    #The larger group of wells must be evenly divisible by the smaller group.
    #Many-to-many
    '''
    right_pipette.transfer(
        volume=[50, 30, 20, 30, 40],
        source=[plate["A1"],plate["A2"]],
        dest=[plate["B1"], plate["B2"], plate["B3"]],
        )
    '''
    #这样操作是不行的，因为较长的列表dest[]有3个，不能被较短列表source[]整除，更别谈volume有5个元素。volume的元素个数是必须要和移液（transfer）次数相一致的
    #In a transfer() or transfer_with_liquid_class(), there's no requirement that the source and destination lists be mutually exclusive. In fact, this command adapted from the tutorial deliberately uses slices of the same list, saved to the variable row, with the effect that each aspiration happens in the same location as the previous dispense:
    row = plate.rows()[0]
    right_pipette.transfer(
        volume=34,
        source=row[:11],
        dest=row[1:],
        )
    #这样就一一对应，A1-A2,A2-A3,A3-A4……
    #在完成一个transfer动作前，是不会换枪头的，默认new_tip = "once"
    #For a transfer(), you can specify different numbers of source and destination wells. In this case, transfer() will always aspirate and dispense as many times as there are wells in the longer list. The shorter list will be "stretched" to cover the length of the longer list. Here is an example of transferring from 3 wells to a full row of 12 wells:
    right_pipette.transfer(
        volume=34,
        source=[plate["A1"], plate["A2"], plate["A3"]],
        dest=plate.rows()[1],
        )
    #这样就一四对应，A1-B1/B2/B3/B4,A2-B5/B6/B7/B8……
    #This is why the longer list must be evenly divisible by the shorter list. Changing the destination in this example to a column instead of a row will cause the API to raise an error, because 8 is not evenly divisible by 3:
    '''
    right_pipette.transfer(
        volume=50,
        source=[plate["A1"], plate["A2"], plate["A3"]],
        dest=plate.columns()[3],  # labware column 4
        )
    '''
    # error: source and destination lists must be divisible
    #这就是99行出现的error
    #The API raises this error rather than presuming which wells to aspirate from three times and which only two times. If you want to aspirate three times from A1, three times from A2, and two times from A3, use multiple transfer() commands in sequence:
    right_pipette.transfer(55, plate["A1"], plate.columns()[3][:3])
    #A1孔移到第4列的1-3行（ABC行，左闭右开区间）
    right_pipette.transfer(55, plate["A2"], plate.columns()[3][3:6])
    #A1孔移到第4列的4-6行（DEF行，左闭右开区间）
    right_pipette.transfer(55, plate["A3"], plate.columns()[3][6:])
    #A1孔移到第4列的7-8行（GH行，左闭右开区间）
    #这里用一些妖尼阁楼头的数字，这样后面模拟的时候就知道在哪一步了
    
    #Finally, be aware of the ordering of source and destination lists when constructing them with well accessor（存储器） methods. For example, at first glance this code may appear to take liquid from each well in the first row of a plate and move it to each of the other wells in the same column:
    right_pipette.transfer(
        volume=22,
        source=plate.rows()[0],
        dest=plate.rows()[1:],
        )
    #A1-B1~B7,A2-B8~C2
    #plate.rows()[0]:A1-A12,12well，而plate.rows()[1:]:7row*12column=84，1well-7wells
    #However, because the well ordering of Labware.rows goes across the plate instead of down the plate, liquid from A1 will be dispensed in B1–B7, liquid from A2 will be dispensed in B8–C2, etc. The intended task is probably better accomplished by repeating transfers in a for loop:
    for i in range(12):
        right_pipette.transfer(
            volume=27,
            source=plate.rows()[0][i],
            dest=plate.columns()[i][1:],
            )
    #Here the repeat index i picks out:
    #The individual well in the first row, for the source.
    #The corresponding column, which is sliced to form the destination.
    #这样i列就和i行对应起来了，就可以直接去取第一行的A2，然后打到2列的B-H行
    #所以最稳妥的办法还是用index i来标记行列，增加代码可读性



