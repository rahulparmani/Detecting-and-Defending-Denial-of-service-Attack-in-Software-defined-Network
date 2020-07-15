# Copyright 2011-2012 James McCauley
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
An L2 learning switch.

It is derived from one written live for an SDN crash course.
It is somwhat similar to NOX's pyswitch in that it installs
exact-match rules for each flow.
"""

from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.util import dpid_to_str, str_to_dpid
from pox.lib.util import str_to_bool
import time

log = core.getLogger()

# We don't want to flood immediately when a switch connects.
# Can be overriden on commandline.
_flood_delay = 0
switch_count=4
host_count=8
#w=20.0
w_min=20.0
w_max=50.0
w=w_min+((w_max-w_min)*0.8)
gamma=[[0,0],[0,0],[0,0],[0,0]]
beta_switch=[0 for i in range(switch_count)]
beta=sum(beta_switch)
alpha_switch=[(w//4) for i in range(switch_count)]
t_switch=[0 for i in range(switch_count)]
lamda_switch=[1 for i in range(switch_count)]
T=5
T_b=20
import datetime, threading
start=time.time()

next_call = time.time()
def thresold_candidate():
      global next_call
      global w
      global t_switch
      global lamda_switch
      global switch_count
      #print(t_switch,time.time())
      for i in range(switch_count):
        #print(1.0/2.0)
        #print(lamda_switch[i]/sum(lamda_switch))
        t_switch[i]=(w*(float(lamda_switch[i])/float(sum(lamda_switch))))
        #print(t_switch,w)
      next_call = next_call+T
      threading.Timer( next_call - time.time(), thresold_candidate ).start()
def update_beta():
      global next_call
      global beta
      global gamma
      gamma=[[0,0],[0,0],[0,0],[0,0]]
      beta=0
      next_call = next_call+T_b
      threading.Timer( next_call - time.time(), update_beta ).start()


thresold_candidate()

class LearningSwitch (object):
  """
  The learning switch "brain" associated with a single OpenFlow switch.

  When we see a packet, we'd like to output it on a port which will
  eventually lead to the destination.  To accomplish this, we build a
  table that maps addresses to ports.

  We populate the table by observing traffic.  When we see a packet
  from some source coming from some port, we know that source is out
  that port.

  When we want to forward traffic, we look up the desintation in our
  table.  If we don't know the port, we simply send the message out
  all ports except the one it came in on.  (In the presence of loops,
  this is bad!).

  In short, our algorithm looks like this:

  For each packet from the switch:
  1) Use source address and switch port to update address/port table
  2) Is transparent = False and either Ethertype is LLDP or the packet's
     destination address is a Bridge Filtered address?
     Yes:
        2a) Drop packet -- don't forward link-local traffic (LLDP, 802.1x)
            DONE
  3) Is destination multicast?
     Yes:
        3a) Flood the packet
            DONE
  4) Port for destination address in our address/port table?
     No:
        4a) Flood the packet
            DONE
  5) Is output port the same as input port?
     Yes:
        5a) Drop packet and similar ones for a while
  6) Install flow table entry in the switch so that this
     flow goes out the appopriate port
     6a) Send the packet out appropriate port
  """
  
  

  
  def __init__ (self, connection, transparent):
    # Switch we'll be adding L2 learning switch capabilities to
    self.connection = connection
    self.transparent = transparent

    # Our table
    self.macToPort = {}

    # We want to hear PacketIn messages, so we listen
    # to the connection
    connection.addListeners(self)

    # We just use this to know when to log a helpful message
    self.hold_down_expired = _flood_delay == 0

    #log.debug("Initializing LearningSwitch, transparent=%s",
    #          str(self.transparent))

  def _handle_PacketIn(self, event):
    """
    Handle packet in messages from the switch to implement above algorithm.
    """
    def drop (duration = None):
      """
      Drops this packet and optionally installs a flow to continue
      dropping similar ones for a while
      """
      if duration is not None:
        if not isinstance(duration, tuple):
          duration = (duration,duration)
        msg = of.ofp_flow_mod()
        msg.match = of.ofp_match.from_packet(packet)
        msg.idle_timeout = duration[0]
        msg.hard_timeout = duration[1]
        msg.buffer_id = event.ofp.buffer_id
        self.connection.send(msg)
      elif event.ofp.buffer_id is not None:
        msg = of.ofp_packet_out()
        msg.buffer_id = event.ofp.buffer_id
        msg.in_port = event.port
        self.connection.send(msg)
    packet = event.parsed
    switch_id=1
    host_id=1
    if packet.src.to_str()=="3e:d5:57:b2:a2:c0":
      switch_id=0
      host_id=0
    elif packet.src.to_str()=="06:f6:74:01:ea:fb":
      switch_id=0
      host_id=1
    elif packet.src.to_str()=="ee:22:79:b9:3e:11":
      switch_id=1
      host_id=0
    elif packet.src.to_str()=="2a:45:3f:89:0e:07":
      switch_id=1
      host_id=1
    elif packet.src.to_str()=="7a:28:f7:af:c0:a3":
      switch_id=2
      host_id=0
    elif packet.src.to_str()=="5a:77:17:1a:16:08":
      switch_id=2
      host_id=1
    elif packet.src.to_str()=="d6:68:86:5d:68:fa":
      switch_id=3
      host_id=0
    elif packet.src.to_str()=="ea:74:64:02:02:34":
      switch_id=3
      host_id=1


    
    global gamma
    global beta_switch
    global beta
    global t_switch
    global lamda_switch
    global start
    
    gamma[switch_id][host_id]+=1
    beta_switch[switch_id]+=1
    lamda_switch[switch_id]+=1
    beta+=1
    print("rho:",0.8)
    print("omega:",w)
    print("Beta:",beta)
    print("beta_switch:",beta_switch)
    print("gamma:",gamma)
    print("alpha_switch:",alpha_switch)
    
    if beta_switch[switch_id]>alpha_switch[switch_id]:
      if beta>w:
        #dos detected
        print("Time to detect dos:",time.time()-start)
        print("Dos attack detected at switch:",switch_id)
        drop(3000)
      else:
        #switch thresold exceeded but not dos 
        print("Thresolds for switch:",switch_id,"is updated from ",alpha_switch[switch_id]," to ",t_switch[switch_id])
        alpha_switch[switch_id]=t_switch[switch_id]


    def flood (message = None):
      """ Floods the packet """
      msg = of.ofp_packet_out()
      if time.time() - self.connection.connect_time >= _flood_delay:
        # Only flood if we've been connected for a little while...

        if self.hold_down_expired is False:
          # Oh yes it is!
          self.hold_down_expired = True
          log.info("%s: Flood hold-down expired -- flooding",
              dpid_to_str(event.dpid))

        if message is not None: log.debug(message)
        #log.debug("%i: flood %s -> %s", event.dpid,packet.src,packet.dst)
        # OFPP_FLOOD is optional; on some switches you may need to change
        # this to OFPP_ALL.
        msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
      else:
        pass
        #log.info("Holding down flood for %s", dpid_to_str(event.dpid))
      msg.data = event.ofp
      msg.in_port = event.port
      self.connection.send(msg)

    
  
    self.macToPort[packet.src] = event.port # 1
    #port = self.macToPort[packet.dst]
    print("packet.src,packet.dst,dpid_to_str(event.dpid), event.port",packet.src.to_str(),packet.dst,dpid_to_str(event.dpid), event.port)
    if not self.transparent: # 2
      if packet.type == packet.LLDP_TYPE or packet.dst.isBridgeFiltered():
        drop() # 2a
        return

    if packet.dst.is_multicast:
      flood() # 3a
    else:
      if packet.dst not in self.macToPort: # 4
        flood("Port for %s unknown -- flooding" % (packet.dst,)) # 4a
      else:
        port = self.macToPort[packet.dst]
        if port == event.port: # 5
          # 5a
          log.warning("Same port for packet from %s -> %s on %s.%s.  Drop."
              % (packet.src, packet.dst, dpid_to_str(event.dpid), port))
          drop(10)
          return
        # 6
        log.debug("installing flow for %s.%i -> %s.%i" %
                  (packet.src, event.port, packet.dst, port))
        msg = of.ofp_flow_mod()
        msg.match = of.ofp_match.from_packet(packet, event.port)
        msg.idle_timeout = 10
        msg.hard_timeout = 30
        msg.actions.append(of.ofp_action_output(port = port))
        msg.data = event.ofp # 6a
        self.connection.send(msg)


class l2_learning (object):
  """
  Waits for OpenFlow switches to connect and makes them learning switches.
  """
  def __init__ (self, transparent, ignore = None):
    """
    Initialize

    See LearningSwitch for meaning of 'transparent'
    'ignore' is an optional list/set of DPIDs to ignore
    """
    core.openflow.addListeners(self)
    self.transparent = transparent
    self.ignore = set(ignore) if ignore else ()

  def _handle_ConnectionUp (self, event):
    if event.dpid in self.ignore:
      log.debug("Ignoring connection %s" % (event.connection,))
      return
    log.debug("Connection %s" % (event.connection,))
    LearningSwitch(event.connection, self.transparent)


def launch (transparent=False, hold_down=_flood_delay, ignore = None):
  """
  Starts an L2 learning switch.
  """
  try:
    global _flood_delay
    _flood_delay = int(str(hold_down), 10)
    assert _flood_delay >= 0
  except:
    raise RuntimeError("Expected hold-down to be a number")

  if ignore:
    ignore = ignore.replace(',', ' ').split()
    ignore = set(str_to_dpid(dpid) for dpid in ignore)

  core.registerNew(l2_learning, str_to_bool(transparent), ignore)