# Copyright (C) 2015 The bitcoin-blockchain-parser developers
#
# This file is part of bitcoin-blockchain-parser.
#
# It is subject to the license terms in the LICENSE file found in the top-level
# directory of this distribution.
#
# No part of bitcoin-blockchain-parser, including this file, may be copied,
# modified, propagated, or distributed except according to the terms contained
# in the LICENSE file.

from .utils import decode_varint, decode_uint32, double_sha256, format_hash
from .input import Input
from .output import Output


class Transaction(object):
    """Represents a bitcoin transaction"""

    def __init__(self, raw_hex):
        self._hash = None
        self.inputs = None
        self.outputs = None
        self._version = None
        self._locktime = None

        offset = 4
        n_inputs, varint_size = decode_varint(raw_hex[offset:])
        offset += varint_size

        self.inputs = []
        for i in range(n_inputs):
            input = Input.from_hex(raw_hex[offset:])
            offset += input.size
            self.inputs.append(input)

        n_outputs, varint_size = decode_varint(raw_hex[offset:])
        offset += varint_size

        self.outputs = []
        for i in range(n_outputs):
            output = Output.from_hex(raw_hex[offset:])
            offset += output.size
            self.outputs.append(output)

        self.size = offset + 4
        self.hex = raw_hex[:self.size]

    def __repr__(self):
        return "Transaction(%s)" % self.hash

    @classmethod
    def from_hex(cls, hex):
        return cls(hex)

    @property
    def version(self):
        """Returns the transaction's version number"""
        if self._version is None:
            self._version = decode_uint32(self.hex[:4])
        return self._version

    @property
    def locktime(self):
        """Returns the transaction's locktime as an int"""
        if self._locktime is None:
            self._locktime = decode_uint32(self.hex[-4:])
        return self._locktime

    @property
    def hash(self):
        """Returns the transaction's hash"""
        if self._hash is None:
            self._hash = format_hash(double_sha256(self.hex))
        return self._hash

    def is_coinbase(self):
        """Returns whether the transaction is a coinbase transaction"""
        for input in self.inputs:
            if input.transaction_hash == "0" * 64:
                return True
        return False

    def uses_replace_by_fee(self):
        """Returns whether the transaction opted-in for RBF"""
        # Coinbase transactions may have a sequence number that signals RBF
        # but they cannot use it as it's only enforced for non-coinbase txs
        if self.is_coinbase():
            return False

        # A transactions opts-in for RBF when having an input
        # with a sequence number < MAX_INT - 1
        for input in self.inputs:
            if input.sequence_number < 4294967294:
                return True
        return False
