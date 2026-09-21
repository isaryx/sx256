# SX256

ZMK user config for a 5×12 split keyboard on Seeed XIAO BLE (`seeeduino_xiao_ble`).

Firmware is pinned to ZMK **v0.3**. GitHub Actions builds `sx_256_left` and `sx_256_right` on push.

## Layout

See [`keymap-drawer/sx_256.svg`](keymap-drawer/sx_256.svg). Source keymap: [`config/boards/shields/sx_256/sx_256.keymap`](config/boards/shields/sx_256/sx_256.keymap).

To regenerate the diagram:

```sh
python3 scripts/keymap_to_drawer.py --draw
```

## References

- [Seeed XIAO BLE hardware overview](https://wiki.seeedstudio.com/XIAO_BLE/#hardware-overview)
- [ZMK new shield](https://zmk.dev/docs/development/new-shield)
- [ZMK keycodes](https://zmk.dev/docs/codes)
