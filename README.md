# Home Assistant Virtual Devices Component

A Home Assistant custom integration that creates virtual devices backed by
existing `switch` and `binary_sensor` entities. Useful for exposing raw
relays/contacts as more meaningful entities without extra hardware.

## Installation

### HACS
Add this repository as a custom repository in HACS (category: Integration),
install "Virtual Devices", then restart Home Assistant.

### Manual
Copy `custom_components/virtual_devices` into your Home Assistant `config/custom_components`
folder, then restart Home Assistant.

## Configuration

Go to **Settings > Devices & Services > Add Integration** and search for
**Virtual Devices**. Each time you add it, you create one virtual device.
Repeat to add as many as you need.

### Cover

Controlled by two switches and simulated with a travel time (no physical
position feedback):

- **Open switch** – turned on while the cover is opening
- **Close switch** – turned on while the cover is closing
- **Stop switch** *(optional)* – pulsed to stop movement; if omitted, both
  open/close switches are simply turned off
- **Full travel time** – seconds needed to move from fully closed to fully
  open, used to estimate position while moving

Supports open, close, stop and set-position.

### Valve

A single switch that opens/closes the valve. The valve's open/closed state
mirrors the underlying switch's own reported state.

### Light (on/off only)

A single switch exposed as an on/off light. State mirrors the underlying
switch's state.

### Button

Input-only: watches a `binary_sensor` and turns its press/release pattern
into `event` entity signals:

- `single_press`
- `double_press`
- `long_press`

Configurable **long press threshold** and **double click window** (both in
milliseconds) control how presses are classified.

