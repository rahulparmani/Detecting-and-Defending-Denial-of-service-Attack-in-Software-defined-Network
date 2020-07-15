from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host
from mininet.node import OVSKernelSwitch
from mininet.node import IVSSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Intf

def MyNetwork2():
    net= Mininet(topo=None, build=False , ipBase='10.0.0.0/8' , link=TCLink)

    info("****Adding Controller")

    poxController = net.addController(name='poxController' ,
                                 controller=RemoteController ,
                                 ip='127.0.0.1',
                                 port=6636)
   

    info('****Now Adding Four Switches')
   
    switch1=net.addSwitch('switch1')
    switch2=net.addSwitch('switch2')
    switch3=net.addSwitch('switch3')
    switch4=net.addSwitch('switch4')

    info('****Now Adding Eight Hosts')

    host1=net.addHost('h1', ip='10.0.0.1/8')
    host2=net.addHost('h2', ip='10.0.0.2/8')
    host3=net.addHost('h3', ip='10.0.0.3/8')
    host4=net.addHost('h4', ip='10.0.0.4/8')
    host5=net.addHost('h5', ip='10.0.0.5/8')
    host6=net.addHost('h6', ip='10.0.0.6/8')
    host7=net.addHost('h7', ip='10.0.0.7/8')
    host8=net.addHost('h8', ip='10.0.0.8/8')

    
    net.addLink(switch1,switch2)
    net.addLink(switch2,switch3)
    net.addLink(switch3,switch4)

    net.addLink(host1,switch1)
    net.addLink(host2,switch1)
    net.addLink(host3,switch2)
    net.addLink(host4,switch2)

    net.addLink(host5,switch3)
    net.addLink(host6,switch3)
    net.addLink(host7,switch4)
    net.addLink(host8,switch4)

    net.build()

    for controller in net.controllers:
        controller.start()

    net.get('switch1').start([poxController])
    net.get('switch2').start([poxController])
    net.get('switch3').start([poxController])
    net.get('switch4').start([poxController])


    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    MyNetwork2()
