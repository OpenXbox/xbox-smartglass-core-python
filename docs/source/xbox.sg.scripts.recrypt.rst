Recrypt binary smartglass data
==============================

Recrypt smartglass packet binaries (useful for test data).

Usage:
::

    usage: xbox-recrypt [-h] src_path src_secret dst_path dst_secret

    Re-Encrypt raw smartglass packets from a given filepath

    positional arguments:
      src_path    Path to sourcefiles
      src_secret  Source shared secret in hex-format
      dst_path    Path to destination
      dst_secret  Target shared secret in hex-format

    optional arguments:
      -h, --help  show this help message and exit

Example:
::

    xbox-recrypt dir_with_src_blobs/ 0011223344..FF dest_dir_recrypted/ FF00FF00FF00FF..FF
