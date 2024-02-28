from struct import pack, unpack

class PConnector(object):
    """
        Multi-stream connector that writes/reads multiple TCP (data)streams
        
        written to be compatible with the JPARSS library, which is
        Copyright (c) 2001 Southeastern Universities Research Association,
        Thomas Jefferson National Accelerator Facility
    """

    def __init__(self, inputs=[], outputs=[], key=None, algo="BLOWFISH", compress=False):
        self._inputs = []
        self._outputs = []
        self.encrypt = key is not None
        if len(inputs)>0 and len(outputs)>0 and len(inputs)!=len(outputs):
            raise ValueError()
        if self.encrypt:
            import pyuftp.cryptutils
        for conn in inputs:
            f = conn.makefile("rb")
            if self.encrypt:
                cipher = pyuftp.cryptutils.create_cipher(key, algo)
                self._inputs.append(pyuftp.cryptutils.DecryptReader(f, cipher))
            else:
                self._inputs.append(f)
        for conn in outputs:
            f = conn.makefile("wb")
            if self.encrypt:
                cipher = pyuftp.cryptutils.create_cipher(key, algo)
                self._outputs.append(pyuftp.cryptutils.CryptWriter(f, cipher))
            else:
                self._outputs.append(f)
        self.seq = 0
        if compress:
            raise ValueError("Not yet implemented")

    def write(self, data):
        """ Write all the data to remote channel """
        _magic = 0xcebf
        size = len(data)
        num_streams = len(self._outputs)
        chunk = int(len(data) / num_streams)
        i = 0
        for out in self._outputs:
            offset = i * chunk
            if i == (num_streams - 1):
                chunk_len = size - i * chunk
            else:
                chunk_len = chunk
            self._write_block(pack(">HHIII", _magic, i, self.seq, size, chunk_len)
                             +data[offset:offset+chunk_len], out)
            i += 1
        self.seq += 1
        return size
    
    def flush(self):
        pass

    def _write_block(self, data, _out):
        to_write = len(data)
        write_offset = 0
        while to_write > 0:
            written = _out.write(data[write_offset:])
            if written is None:
                written = 0
            write_offset += written
            to_write -= written
        _out.flush()
    
    def _read_block(self, length, _in):
        _chunks = []
        _have = 0
        while _have < length:
            want = min(length - _have, length)
            chunk = _in.read(want)
            if chunk == b'':
                break
            _chunks.append(chunk)
            _have = _have + len(chunk)
        return b''.join(_chunks)

    def read(self, length):
        """ Read data from remote channel """
        buffer = bytearray(length)
        _magic = 0xcebf
        num_streams = len(self._inputs)
        for i in range(0, num_streams):
            src = self._inputs[i]
            header = self._read_block(16, src)
            if len(header)==0:
                # EOF
                return []
            (magic, pos, seq, size, chunk_len) = unpack(">HHIII", header)
            if pos!=i:
                raise Exception("I/O error reader %s (unexpected stream position: %s)" % (i,pos))
            if magic!=_magic:
                raise Exception("I/O error reader %s (magic number)" % i)
            if seq!=self.seq:
                raise Exception("I/O error reader %s (sequence number)" % i)
            chunk = int(size / num_streams)
            offset = pos * chunk
            buffer[offset:offset+chunk_len] = self._read_block(chunk_len, src)
        self.seq += 1
        return buffer[0:size]

    def close(self):
        for c in self._inputs:
            try:
                c.close()
            except:
                pass
        for c in self._outputs:
            try:
                c.close()
            except:
                pass