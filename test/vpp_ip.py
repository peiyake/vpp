"""
  IP Types

"""
import logging

from ipaddress import ip_address
from socket import AF_INET, AF_INET6
from vpp_papi import VppEnum
try:
    text_type = unicode
except NameError:
    text_type = str

_log = logging.getLogger(__name__)


class DpoProto:
    DPO_PROTO_IP4 = 0
    DPO_PROTO_IP6 = 1
    DPO_PROTO_MPLS = 2
    DPO_PROTO_ETHERNET = 3
    DPO_PROTO_BIER = 4
    DPO_PROTO_NSH = 5


INVALID_INDEX = 0xffffffff


class VppIpAddressUnion():
    def __init__(self, addr):
        self.addr = addr
        self.ip_addr = ip_address(text_type(self.addr))

    def encode(self):
        if self.version == 6:
            return {'ip6': self.ip_addr}
        else:
            return {'ip4': self.ip_addr}

    @property
    def version(self):
        return self.ip_addr.version

    @property
    def address(self):
        return self.addr

    @property
    def length(self):
        return self.ip_addr.max_prefixlen

    @property
    def bytes(self):
        return self.ip_addr.packed

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.ip_addr == other.ip_addr
        elif hasattr(other, "ip4") and hasattr(other, "ip6"):
            # vl_api_address_union_t
            if 4 == self.version:
                return self.ip_addr.packed == other.ip4
            else:
                return self.ip_addr.packed == other.ip6
        else:
            _log.error("Comparing VppIpAddressUnions:%s"
                       " with incomparable type: %s",
                       self, other)
            return NotImplemented

    def __str__(self):
        return str(self.ip_addr)


class VppIpAddress():
    def __init__(self, addr):
        self.addr = VppIpAddressUnion(addr)

    def encode(self):
        if self.addr.version == 6:
            return {
                'af': VppEnum.vl_api_address_family_t.ADDRESS_IP6,
                'un': self.addr.encode()
            }
        else:
            return {
                'af': VppEnum.vl_api_address_family_t.ADDRESS_IP4,
                'un': self.addr.encode()
            }

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.addr == other.addr
        elif hasattr(other, "af") and hasattr(other, "un"):
            # a vp_api_address_t
            if 4 == self.version:
                return other.af == \
                    VppEnum.vl_api_address_family_t.ADDRESS_IP4 and \
                    other.un == self.addr
            else:
                return other.af == \
                    VppEnum.vl_api_address_family_t.ADDRESS_IP6 and \
                    other.un == self.addr
        else:
            _log.error(
                "Comparing VppIpAddress:<%s> %s with incomparable "
                "type: <%s> %s",
                self.__class__.__name__, self,
                other.__class__.__name__, other)
            return NotImplemented

    def __ne__(self, other):
        return not (self == other)

    def __str__(self):
        return self.address

    @property
    def bytes(self):
        return self.addr.bytes

    @property
    def address(self):
        return self.addr.address

    @property
    def length(self):
        return self.addr.length

    @property
    def version(self):
        return self.addr.version

    @property
    def is_ip6(self):
        return (self.version == 6)

    @property
    def af(self):
        if self.version == 6:
            return AF_INET6
        else:
            return AF_INET

    @property
    def dpo_proto(self):
        if self.version == 6:
            return DpoProto.DPO_PROTO_IP6
        else:
            return DpoProto.DPO_PROTO_IP4


class VppIpPrefix():
    def __init__(self, addr, len):
        self.addr = VppIpAddress(addr)
        self.len = len

    def __eq__(self, other):
        if self.address == other.address and self.len == other.len:
            return True
        return False

    def encode(self):
        return {'address': self.addr.encode(),
                'len': self.len}

    @property
    def version(self):
        return self.addr.version

    @property
    def address(self):
        return self.addr.address

    @property
    def bytes(self):
        return self.addr.bytes

    @property
    def length(self):
        return self.len

    @property
    def is_ip6(self):
        return self.addr.is_ip6

    def __str__(self):
        return "%s/%d" % (self.address, self.length)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (self.len == other.len and self.addr == other.addr)
        elif hasattr(other, "address") and hasattr(other, "len"):
            # vl_api_prefix_t
            return self.len == other.len and \
                   self.addr == other.address
        else:
            _log.error(
                "Comparing VppIpPrefix:%s with incomparable type: %s" %
                (self, other))
            return NotImplemented


class VppIpMPrefix():
    def __init__(self, saddr, gaddr, glen):
        self.saddr = saddr
        self.gaddr = gaddr
        self.glen = glen
        self.ip_saddr = VppIpAddressUnion(text_type(self.saddr))
        self.ip_gaddr = VppIpAddressUnion(text_type(self.gaddr))
        if self.ip_saddr.version != self.ip_gaddr.version:
            raise ValueError('Source and group addresses must be of the '
                             'same address family.')

    def encode(self):
        if 6 == self.ip_saddr.version:
            prefix = {
                'af': VppEnum.vl_api_address_family_t.ADDRESS_IP6,
                'grp_address': {
                    'ip6': self.gaddr
                },
                'src_address': {
                    'ip6': self.saddr
                },
                'grp_address_length': self.glen,
            }
        else:
            prefix = {
                'af': VppEnum.vl_api_address_family_t.ADDRESS_IP4,
                'grp_address': {
                    'ip4': self.gaddr
                },
                'src_address': {
                    'ip4':  self.saddr
                },
                'grp_address_length': self.glen,
            }
        return prefix

    @property
    def length(self):
        return self.glen

    @property
    def version(self):
        return self.ip_gaddr.version

    def __str__(self):
        return "(%s,%s)/%d" % (self.saddr, self.gaddr, self.glen)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return (self.glen == other.glen and
                    self.ip_saddr == other.ip_gaddr and
                    self.ip_saddr == other.ip_saddr)
        elif (hasattr(other, "grp_address_length") and
              hasattr(other, "grp_address") and
              hasattr(other, "src_address")):
            # vl_api_mprefix_t
            if 4 == self.ip_saddr.version:
                if self.glen == other.grp_address_length and \
                   self.gaddr == str(other.grp_address.ip4) and \
                   self.saddr == str(other.src_address.ip4):
                    return True
                return False
            else:
                return (self.glen == other.grp_address_length and
                        self.gaddr == other.grp_address.ip6 and
                        self.saddr == other.src_address.ip6)
        else:
            raise Exception("Comparing VppIpPrefix:%s with unknown type: %s" %
                            (self, other))
        return False
