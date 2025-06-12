"""Configures a collection of nodes for running Homa experiments.

Instructions:
None
"""

import geni.portal as portal
import geni.rspec.pg as rspec
import geni.rspec.emulab

pc = portal.Context()
# rspec = pg.Request()
request = pc.makeRequestRSpec()

pc.defineParameter("node_type", "Type of nodes",
portal.ParameterType.NODETYPE, "xl170", legalValues=[("c6620", "c6620"),
                                                     ("c6525-100g", "c6525-100g"),
                                                     ("c6525-25g", "c6525-25g"),
                                                     ("d6515", "d6515"),
                                                     ("m400", "m400"),
                                                     ("m510", "m510"),
                                                     ("pc3000", "pc3000"),
                                                     ("xl170", "xl170"),
                                                     ], advanced=False, groupId=None)
pc.defineParameter("num_nodes", "Number of nodes to use.<br> Check cluster availability <a href=\"https://www.cloudlab.us/cluster-graphs.php\">here</a>.",
        portal.ParameterType.INTEGER, 2, advanced=False, groupId=None)

# The possible set of base disk-images that this cluster can be booted with.
# The second field of every tuple is what is displayed on the cloudlab
# dashboard.
images = [ ("homa6139", "Ubuntu 24 with 6.13.9 kernel"),
           ("net-next", "Ubuntu 22 with net-next kernel"),
           ("homa6106", "Ubuntu 22 with 6.10.6 kernel"),
           ("homa6138", "Ubuntu 22 with 6.1.38 kernel"),
           ("ouster5177v9", "Ubuntu 22 with 5.17.7 kernel"),
           ("ouster5177v8", "ouster 5.17.7 v8"),
           ("ouster5480v4", "ouster 5.4.80 v4"),
           ("ouster_5.4.3_v3", "ouster 5.4.3 v3"),
           ("ouster_4.15.18_v13", "ouster 4.15.18_v13"),
           ("Ubuntu 22", "Ubuntu 22"),
           ("Ubuntu 20.04", "Ubuntu 20.04") ]
imageUrns = {}
imageUrns["homa6139"] = "urn:publicid:IDN+utah.cloudlab.us+image+homa-PG0:homa6139"
imageUrns["net-next"] = "urn:publicid:IDN+utah.cloudlab.us+image+homa-PG0:net-next"
imageUrns["homa6106"] = "urn:publicid:IDN+utah.cloudlab.us+image+homa-PG0:homa6106"
imageUrns["homa6138"] = "urn:publicid:IDN+utah.cloudlab.us+image+homa-PG0:homa6138"
imageUrns["ouster5177v9"] = "urn:publicid:IDN+utah.cloudlab.us+image+homa-PG0:ouster5177v9"
imageUrns["ouster5177v8"] = "urn:publicid:IDN+utah.cloudlab.us+image+ramcloud-PG0:ouster5177v8"
imageUrns["ouster5480v4"] = "urn:publicid:IDN+utah.cloudlab.us+image+ramcloud-PG0:ouster5480v4"
imageUrns["ouster_5.4.3_v3"] = "urn:publicid:IDN+utah.cloudlab.us+image+ramcloud-PG0:ouster_5.4.3_v3"
imageUrns["ouster_4.15.18_v13"] = "urn:publicid:IDN+utah.cloudlab.us+image+ramcloud-PG0:ouster_4.15.18_v13"
imageUrns["Ubuntu 22"] = "urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU22-64-STD"
imageUrns["Ubuntu 20.04"] = "urn:publicid:IDN+emulab.net+image+emulab-ops//UBUNTU20-64-STD"
pc.defineParameter("image", "Disk Image",
        portal.ParameterType.IMAGE, images[0], images,
        "The disk image used to boot cluster nodes.")
pc.defineParameter("switch", "Preferred switch", portal.ParameterType.STRING, "None", advanced=False, groupId=None,
        legalValues=[("None", "None"),
                     ("xl170-rack1", "xl170-rack1 (hp001-040)"),
                     ("xl170-rack2", "xl170-rack2 (hp041-080)"),
                     ("xl170-rack3", "xl170-rack3 (hp081-120)"),
                     ("xl170-rack4", "xl170-rack4 (hp121-160)"),
                     ("xl170-rack5", "xl170-rack5 (hp161-200)")])

pc.defineParameter("attachOusterDataset", "Attach /ouster dataset to node0",
        portal.ParameterType.BOOLEAN, True)
pc.defineParameter("attachNetnextDataset", "Attach /netnext dataset to node0",
        portal.ParameterType.BOOLEAN, True)
pc.defineParameter("cloneDatasets", "Clone dataset(s) before attaching",
        portal.ParameterType.BOOLEAN, False)
params = pc.bindParameters()
pc.verifyParameters()

lan = request.LAN("lan1")
lan.best_effort = True
lan.link_multiplexing = True
lan.setJumboFrames()

for i in range(params.num_nodes):
    node = request.RawPC("node%s" % i)
    node.hardware_type = params.node_type
    node.disk_image = imageUrns[params.image]
    if params.switch != "None":
        node.Desire(params.switch, 1.0)

    node.addService(rspec.Execute(shell="bash", command="/local/setup_ssh.sh"))

    if1 = node.addInterface("if1")
    ip1 = "10.0.1." + str(i+1)
    if1.addAddress(rspec.IPv4Address(ip1, "255.255.255.0"))
    lan.addInterface(if1)

    # Attach datasets on the first node, if requested.
    if i == 0 and params.attachOusterDataset:
        iface = node.addInterface()
        fsnode = request.RemoteBlockstore("fsnode", "/ouster")
        fsnode.dataset = "urn:publicid:IDN+utah.cloudlab.us:ramcloud-pg0+ltdataset+ouster_builds"
        if params.cloneDatasets:
            fsnode.rwclone = True
        fslink = request.Link("fslink")
        fslink.addInterface(iface)
        fslink.addInterface(fsnode.interface)
        fslink.best_effort = True
        fslink.vlan_tagging = True
        fslink.link_multiplexing = True
    if i == 0 and params.attachNetnextDataset:
        iface2 = node.addInterface()
        fsnode2 = request.RemoteBlockstore("fsnode2", "/netnext")
        fsnode2.dataset = "urn:publicid:IDN+utah.cloudlab.us:homa-pg0+ltdataset+ouster_netnext"
        if params.cloneDatasets:
            fsnode2.rwclone = True
        fslink2 = request.Link("fslink2")
        fslink2.addInterface(iface2)
        fslink2.addInterface(fsnode2.interface)
        fslink2.best_effort = True
        fslink2.vlan_tagging = True
        fslink2.link_multiplexing = True

pc.printRequestRSpec(request)
