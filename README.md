[![CC BY-NC-SA 4.0][cc-by-nc-sa-shield]][cc-by-nc-sa]

## Description
Add-In for Fusion 360 allowing quick generation of simple [gridfinity](https://www.youtube.com/watch?v=ra_9zU-mnl8) bins to store Drill Bits. Bins can be generated to hold any number of drill bits, specified by their diameter. By selecting a type of bit (currently HSS, BradPoint, Masonry, or Tile), the add-in can estimate the length of the bits to make for fast generation of bins. Note however that this is based upon published "typical" values, despite including a fair tollerance, you may need to manually provide measurements if your drill bits are of a less-typical dimension.

![](/documentation/assets/gridfinity-drill-bit-storage.png)

## Credits
This add-in utilises the Gridfinity Bin generation code published by Le0Michine as part of his FusionGridfinityGenerator add-in (https://github.com/Le0Michine/FusionGridfinityGenerator/). If you've not already installed it, make sure you check it out. It really is an excellent and invaluable tool, and all credit for the generation of the Gridfinity Bin in this add-in resides with the original author. This add-in extends that brilliant work, by adding the capability to create full drill-storage bins.

## Features

- add bits of varying size to a single Gridfinity compatable bin (limited to a maximum size of 10U x 10U)
- as well as the bin for each sized bit, the bin features a depression, allowing easy retrival of the bits:

![](/documentation/assets/dill-bit-depression.png)

## Generate Dialog

![](/documentation/assets/fusion-dialog-bin-generator.png)

### Drill Bit Type
- select the type of drill bit to be accomodated
- this sets the internal calculations (based upon the drill bit diameter and type)

#### Drill Bits
- this is a table to provide the required bit sizes
- you can add/remove rows as required
- any row with a Bit Diameter of 0 will be ignored
- all sizes are in mm
- the Bit Length column can be left empty, in which case the length will be estimated based upon the diameter, and the selected Bit Type

### Gridfinity Bin Width/Length/Height
- this allows you to automatically, or manually, set the Width, Length, and Height of the generated Gridfinity Bin
- as mentioned in the Credits above, the code used to generate the bins is copied from the excellent work by Le0Michine
- if set to "auto", the add-in will calculate the required size of the bin (in which case the value inputs are disabled, but will show the calculated values)
- if "auto" is disabled, you can set a value manually. If the value entered is too small to accomodate the number/size of drill bits, the UI will error and disable the "Ok" button

### Split Body
- this allows you to automatically split the upper element of the body. This is useful if you want to print the top of the box and the text in a different fillament colour (recommended)
- if you do this, ensure you use filaments that will bond together, mixing different types of filament (PLA/PETG/ABS) wouldn't be recommended

### Gridfinity Bin Utilisation
- whether the size of the bin has been set manually or automatically, this section will show the percentage utilisation of the bin, and is provided only for reference as an indication of remaining space within the bin.

## Roadmap
Some features currently planned:
- customise the number of bits held per bin (and therefore control the height/width of each bin)

If there are other features you would like to see, please leave a feature request!

## Installation

### Via Autodesk App Store

- Once available via the App Store, details will appear here


### From source code
#### Step 1: Download

Download code into a location on your hard drive.
- Option 1: Clone git repository

```
git clone https://github.com/Mobbsey/FusionGridfinityDrillBitStorageGenerator.git
```
- Option 2: Download ZIP file
  - Use [latest release page](https://github.com/Mobbsey/FusionGridfinityDrillBitStorageGenerator/releases) to download ZIP file `GridfinityDrillBitStorageGenerator-vX.X.X.X.zip`. The release page should contain latest stable version. Alternatively you can choose to use `Code / Download ZIP` option.
  - Unpack content of the ZIP file into your target location

#### Step 2: Install as Add-In to Fusion 360
- In Fusion open `Scripts and Add-Ins` window by pressing `Shift + S`.
  - It can also be found in the UI `Design -> Utilities -> ADD-INS`
- Select `Add-Ins` tab and press `+` icon to add new add in
- Select path to the repository downloaded in Step 1. Choose the folder containing `DrillBitGridfinity.py`.
- `DrillBitGridfinity` should appear in the list of add ins
- Select `DrillBitGridfinity` and click `Run` to launch the add in
- `Gridfinity Drill Bit Storage` option should appear in `Create` menu in the Solid body workspace environment, along with a toolbar on the Solid > Create toolbar panel

## Update

To update the script download latest sources into the same location and relaunch Fusion. If you used Autodesk app store to install the addon please follow the same link then download and install the latest version from there.

## Support the project

The plugin is free. However, if you want to support the project you can do so by [buying me a coffe](https://www.buymeacoffee.com/mobbsey).

## Credits
- Fusion Gridfinity Generator by [Le0Michine](https://github.com/Le0Michine/FusionGridfinityGenerator/)
- [Gridfinity](https://www.youtube.com/watch?v=ra_9zU-mnl8) by [Zack Freedman](https://www.youtube.com/c/ZackFreedman/about)

This work is licensed under the same license as Gridfinity, being a
[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License][cc-by-nc-sa].

[![CC BY-NC-SA 4.0][cc-by-nc-sa-image]][cc-by-nc-sa]

[cc-by-nc-sa]: http://creativecommons.org/licenses/by-nc-sa/4.0/
[cc-by-nc-sa-image]: https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png
[cc-by-nc-sa-shield]: https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg
