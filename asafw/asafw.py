import cstruct
import uuid
import os
import io
import sys

# from 0x30 to 0x1cf
class asa_field1(cstruct.CStruct):
    __byte_order__ = cstruct.BIG_ENDIAN
    __struct__ = """
    unsigned char field;
    unsigned short length;
    """

    def __init__(self, string=None, **kargs):
        if string is not None:
            super().__init__(string[0:3])
            if len(string) > 3:
                self.data = string[3:3+self.length]
            else:
                self.data = b''
        else:
            if 'data' in kargs:
                self.data = kargs['data']
                del kargs['data']
            super().__init__(string, **kargs)
    
    def __str__(self):
        cleanup = False
        if 'data' not in self.__fields__:
            self.__fields__.append('data')
            cleanup = True
        result = super().__str__()
        if cleanup:
            self.__fields__.remove('data')
        return result

    def pack(self):
        data_result = b''

        if isinstance(self.data,list):
            for list_item in self.data:
                data_result = bytearray(data_result) + bytearray(list_item.pack())
        else:
            data_result = bytearray(data_result) + bytearray(self.data)

        self.length = len(data_result)
        result = super().pack()

        return bytes(bytearray(result) + bytearray(data_result))

def get_next_field1_header(bin_file):
    return asa_field1(bin_file.read(asa_field1.size))

def get_next_field1_data(bin_file, header):
    return bin_file.read(header.length)   

def parse_field1_headers(bin_file):
    cur_field = 0
    headers = []
    while cur_field < 12:
        header = get_next_field1_header(bin_file)

        if header.field == 3:
            header_3 = header
            header_3.data = []
            while cur_field < 6:
                header = get_next_field1_header(bin_file)
                header.data = get_next_field1_data(bin_file, header)
                header_3.data.append(header)
                cur_field = header.field
            header = header_3
        else:
            header.data = get_next_field1_data(bin_file, header)
        headers.append(header)
        cur_field = header.field

    return headers



def gen_asa_raw_field1_headers(issuer1="CN=CiscoSystems;OU=NCS_Kenton_ASA;O=CiscoSystems", 
                        serial="60A6A3E5", 
                        issuer2="CN=CiscoSystems;OU=NCS_Kenton_ASA;O=CiscoSystems",
                        magic_key=b'\x87\x12z`\xbdx\x892\x8a`\xcf\x91\x1fGK\xd1\xf7\xb1\xe0\ta\xb8\xb7\xa7\x1d\x9fl\x80\x1b\xff\xa9\xd5s\xa7W\x97\xa5#E0\xd7\x1b\xaa\xc9\xa7\xf4\xa4\x8c\x88\xb7\xfe<\xc2@\x91Z\xfb10\xe5\xd0\xf0#e\xfd|c\x16f/\x1b/\xc5\x97\xfc[D\xdd\xc2A\xcb\xc61\xc6j\xf5-w~\\r\xd3\xd8]<\xa5{\xb1\xc9\xad\xe5=\xfb\xaa\x81NIg\xe7\xdd\x17{o\xcbdg?6t\x86\xc01:\x92\x10g\xb4L!8\x02\xd5\x04\x88\xa2\x81&\n\x9c\xde\xf9\x03m=A\r\x07\x11\x17X\x92\xd6\xaex\xd6\xe1\x11\xb3\xe1\xb1m\xa5\xf8\xc8\xa7\\\x7fl\x97\xa3\xd3Yu|\xcaU\xb7\x7f:\xe2\x82N7P\xa2\x96\xff\x03?\xc5\xf5\xcd|\x90\xf4m\xc67\xf0\xd7\xfeq[!\xd4\x1c\xa4\xf0\xbd\x81f\x9eJ>\x83\xf5%}\x8eX\xea\xcf\xd4\x88\xc5\xa5}F\x9a\xbd2\xf1\xbbA\xd0\xc7\x18a\x94\x9b\x96\x0bh\x14L\xa9u\xe5\x19\xfa\x96d\x1f\x01\xee\xbd'):
    headers = [
    asa_field1(field=1, data=b'\x01\x01'),
    asa_field1(field=2, data=b'\x00\x00\x01\x8c'),
    asa_field1(field=3, data=[
        asa_field1(field=4, data=bytes(issuer1,"ascii")),
        asa_field1(field=5, data=bytes(serial,"ascii")),
        asa_field1(field=6, data=bytes(issuer2,"ascii"))]),
    asa_field1(field=7, data=b'\x00'),
    asa_field1(field=8, data=b'\x01'),
    asa_field1(field=9, data=b'\x00'),
    asa_field1(field=10, data=b'\x01'),
    asa_field1(field=11, data=magic_key),
    asa_field1(field=12, data=b'A')]

    result = bytearray()

    for header in headers:
        result += bytearray(header.pack())
    
    result += bytearray(b'\xeb')
    #TODO: move this into the container
    result += bytearray("\00" * (0x1a0 - len(result)), 'ascii')

    return bytes(result)



# starting 0x10 then next is 0x1d0 
class asa_block(cstruct.CStruct):
    __byte_order__ = cstruct.LITTLE_ENDIAN
    __struct__ = """
    unsigned char block_uuid_raw[16];
    unsigned char meta_data_length;
    unsigned char unkown1;
    unsigned int data_length;
    unsigned char unkown2[2];
    unsigned char sub_blocks;
    unsigned char unkown3[7];
    """

    @property
    def MetaDataLength(self):
        return (self.meta_data_length << 4)

    @MetaDataLength.setter
    def MetaDataLength(self, val):
        self.meta_data_length = val >> 4

    @property
    def DataLength(self):
        return (self.data_length >> 4)
    
    @DataLength.setter
    def DataLength(self, val):
        self.data_length = val << 4

    @property
    def UUID(self):
        return uuid.UUID(bytes=bytes(self.block_uuid_raw))
    
    @UUID.setter
    def UUID(self, val):
        if isinstance(val, str):
            self.block_uuid_raw = [int(x) for x in uuid.UUID(val).bytes]
        elif isinstance(val, uuid.UUID):
            self.block_uuid_raw = [int(x) for x in val.bytes]

    @property
    def HasSubBlocks(self):
        return True if self.sub_blocks == 1 else False

    @HasSubBlocks.setter
    def HasSubBlocks(self, val):
        if val == True:
            self.sub_blocks = 1
        else:
            self.sub_blocks = 0


UUID_ASA_FW_BLOB =          uuid.UUID('11bb8d46-d638-014d-a26b-7d66620dfc74')
UUID_MAIN_CONTAINER =       uuid.UUID('60d090eb-09f7-1a4a-9f30-9e45f7287490')
UUID_FW_CONTAINER =         uuid.UUID('71546a9d-ae27-ef42-9798-c3dfbe0dc55e')
UUID_KERNEL_PARAMS =        uuid.UUID('810e04c5-2ed1-2d47-8921-a02bb0006535')
UUID_ROOTFS_FW_BLOCK =      uuid.UUID('1a4dbf47-907c-fc49-9041-cdeba6c3f647')
UUID_BOOT_FW_BLOCK =        uuid.UUID('e1c38579-4a5e-8947-b696-6d75a1835533')
UUID_KERNEL_FW_BLOCK =      uuid.UUID('2b74541d-6e2e-6d48-ad21-fa5271f39b92')

UUID_BOOT_FW_ELF_BLOCK =    uuid.UUID('5343212a-e95f-5142-9ac8-5d831b0a9416')

def get_next_block_header(bin_file):
    return asa_block(bin_file.read(asa_block.size))

def get_next_block_header_meta_data(bin_file, block_header):
    if block_header.MetaDataLength > 0:
        return bin_file.read(block_header.MetaDataLength)
    else:
        return None

def parse_block(bin_file):
    block_header = get_next_block_header(bin_file)
    block_meta_data = None
    if block_header.MetaDataLength > 0:
        block_meta_data = get_next_block_header_meta_data(bin_file, block_header)
        if block_header.UUID == UUID_MAIN_CONTAINER:
            meta_data_bin = io.BytesIO(block_meta_data)
            block_meta_data = parse_field1_headers(meta_data_bin)

    return block_header, block_meta_data

5
class AsaBlock():
    def __init__(self, asa_block_header, meta_data, data):
        self._asa_block_header = asa_block_header
        self._meta_data = meta_data
        self._data = data

    def __str__(self):
        return f"[{self._asa_block_header.UUID}]"
    
    @property
    def children(self):
        child_list = []
        if self._meta_data is not None:
            if isinstance(self._meta_data, list):
                child_list.extend(self._meta_data)
            else:
                child_list.append(self._meta_data)
        if self._data is not None:
            if isinstance(self._data, list):
                child_list.extend(self._data)
            else:
                child_list.append(self._data)
        return child_list
        



def pprint_tree(node, file=None, _prefix="", _last=True):
    print(_prefix, "`- " if _last else "|- ", str(node), sep="", file=file)
    _prefix += "   " if _last else "|  "
    if hasattr(node, "children"):
        child_count = len(node.children)
        for i, child in enumerate(node.children):
            _last = i == (child_count - 1)
            pprint_tree(child, file, _prefix, _last)



def get_blocks_from_file(bin_file, dump_blocks=False):
    header, header_metadata_headers = parse_block(bin_file)
    starting_offset = bin_file.tell()
    current_size = bin_file.tell() - starting_offset
    data = None
    if header.HasSubBlocks:
        data = []
        while current_size < header.DataLength:
            data.append(get_blocks_from_file(bin_file, dump_blocks))
            current_size = bin_file.tell() - starting_offset
    else:
        if header.DataLength > 0:
            data = f"DATA BLOCK [{hex(header.DataLength)}]"
            if dump_blocks:
                data += " " + f"/tmp/{header.UUID}.bin"
                with open(f"/tmp/{header.UUID}.bin", "wb") as output_block_bin:
                    output_block_bin.write(bin_file.read(header.DataLength))
            else:
                bin_file.seek(header.DataLength, os.SEEK_CUR)
    
    return AsaBlock(header, header_metadata_headers, data)

def check_for_asa_fw_blob(bin_file):
    first_uuid = bin_file.read(0x10)
    if uuid.UUID(bytes=first_uuid) != UUID_ASA_FW_BLOB:
        bin_file.seek(0, os.SEEK_SET)

if __name__ == "__main__":
   with open(sys.argv[1], "rb") as bin_file:

       check_for_asa_fw_blob(bin_file)
       pprint_tree(get_blocks_from_file(bin_file, True))

#pos = 0x2a0
#with open("/home/sean/asa5508/ftd-boot-9.16.1.0.lfbff", "rb") as abin:
#    abin.seek(0,2)
#    file_size = abin.tell()
#    print(file_size)
#    while pos < file_size:
#        abin.seek(pos)
#        data_asa2 = abin.read(asa_field2.size)
#        asa_header2 = asa_field2(data_asa2)
#        print(f"[{hex(pos)}] {uuid.UUID(bytes=bytes(asa_header2.field))} ({hex(asa_header2.bits >> 4)})")
#        abin.seek(pos + asa_field2.size)
#        data_segment = abin.read((asa_header2.bits >> 4))
#        with open(f"/tmp/{uuid.UUID(bytes=bytes(asa_header2.field))}","wb") as output_bin:
#            output_bin.write(data_segment)
#        print(len(data_segment))
#        pos += (asa_header2.bits >> 4) + asa_field2.size

