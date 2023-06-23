#!/usr/bin/env python3

import argparse
import asafw.asafw as asafw
import sys



release_key_p = """
96:A2:E6:E4:51:4D:4A:B0:F0:EF:DB:41:82:A6:AC:D0:
FC:11:40:C2:F0:76:10:19:CE:D0:16:7D:26:73:B1:55:
FE:42:FE:5D:5F:4D:A5:D5:29:7F:91:EC:91:4D:9B:33:
54:4B:B8:4D:85:E9:11:2D:79:19:AA:C5:E7:2C:22:5E:
F6:66:27:98:1C:5A:84:5E:25:E7:B9:09:80:C7:CD:F4:
13:FB:32:6B:25:B5:22:DE:CD:DC:BE:65:D5:6A:99:02:
95:89:78:8D:1A:39:A3:14:C9:32:EE:02:4C:AB:25:D0:
38:AD:E4:C9:C6:6B:28:FE:93:C3:0A:FE:90:D4:22:CC:
FF:99:62:25:57:FB:A7:C6:E4:A5:B2:22:C7:35:91:F8:
BB:2A:19:42:85:8F:5E:2E:BF:A0:9D:57:94:DF:29:45:
AA:31:56:6B:7C:C4:5B:54:FE:DE:30:31:B4:FC:4E:0C:
9D:D8:16:DB:1D:3D:8A:98:6A:BB:C2:34:8B:B4:AA:D1:
53:66:FF:89:FB:C2:13:12:7D:5B:60:16:CA:D8:17:54:
7B:41:1D:31:EF:54:DB:49:40:1F:99:FB:18:38:03:EE:
2D:E8:E1:9F:E6:B2:C3:1C:55:70:F4:F3:B2:E7:4A:5A:
F5:AA:1D:03:BD:A1:C3:9F:97:80:E6:63:05:27:F2:1F
"""


def main():
    parser = argparse.ArgumentParser(description="ASA Firmware tool")

    subparser = parser.add_subparsers(required=True)

    extract_parser = subparser.add_parser('extract')
    extract_parser.set_defaults(command='extract')
    extract_parser.add_argument('file', type=str, help="File to extract")
    extract_parser.add_argument('--output-dir', type=str, default='/tmp', help="Directory to extract blocks to")
    extract_parser.add_argument('--display-only',action='store_true', help='Only display blocks (do not extract)')
    
    create_parser = subparser.add_parser('create')
    create_parser.set_defaults(command='create')

    create_subparser = create_parser.add_subparsers(required=True)

    create_boot_parser = create_subparser.add_parser('boot')
    create_boot_parser.set_defaults(create_command='boot')
    create_boot_parser.add_argument('file', type=str, help='Input boot binary to package')
    create_boot_parser.add_argument('--output', type=str, help='Output file')

    create_fw_parser = create_subparser.add_parser('fw')
    create_fw_parser.set_defaults(create_command='fw')
    create_fw_parser.add_argument('--kernel', type=str, help='Input kernel')
    create_fw_parser.add_argument('--rootfs', type=str, help='Input rootfs')
    create_fw_parser.add_argument('--output', type=str, help='Output file')

    args = parser.parse_args()

    if args.command == 'extract':
        with open(args.file, "rb") as bin_file:
            asafw.check_for_asa_fw_blob(bin_file)
            asafw.pprint_tree(asafw.get_blocks_from_file(bin_file, args.output_dir, not args.display_only))
            # asafw.try_hash(bin_file)
    elif args.command == 'create':
        if args.create_command == 'boot':
            with open(args.file, 'rb') as input_block:
                with open(args.output, 'wb') as output_block:
                    asafw.create_boot_block(output_block, input_block)
        if args.create_command == 'fw':
            with open(args.kernel, 'rb') as input_kernel:
                with open(args.rootfs, 'rb') as input_rootfs:
                    with open(args.output, 'wb') as bin_file:
                        asafw.write_asa(bin_file, asafw.gen_blocks(rootfs_block=input_rootfs, kernel_block=input_kernel))
