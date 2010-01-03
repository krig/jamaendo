# Jamaendo

A media player for the Nokia N900 and other Maemo 5 (Fremantle) phones.

[Jamaendo][jamaendo] plays music from the music catalog of [JAMENDO][jamendo].

JAMENDO is an online platform that distributes musical works under
Creative Commons licenses.

Jamaendo is written by Kristoffer Grönlund.

## Panucci

[Jamaendo][jamaendo] is based on [Panucci][panucci], an audiobook and podcast player for
Maemo. Panucci is written by 

 [jamendo]: http://www.jamendo.com/ "Jamendo"
 [jamaendo]: http://jamaendo.garage.maemo.org/ "Jamaendo"
 [panucci]: http://panucci.garage.maemo.org/ "Panucci"

## Installation

To build the packages, you need a scratchbox environment set up. See
the Nokia/Maemo documentation for information on how to do this. To
build the package, go to the Jamaendo source directory and type

    make build-package

This will (hopefully) generate a .deb file for you to install on your
Maemo 5 device.

## Optification

If you're running a newer release of the Fremantle platform, this step
may not (I hope not!) be necessary, but either way: The package that
the build process produces is not entirely optified. It is compatible
with the `maemo-optify` tool, however. All you need to do is run
`maemo-optify-deb` on the generated .deb file.

## License

The backend code that speaks to jamendo.com is in the jamaendo module. This module is licensed under a modified New BSD License (modified to remove attribution clauses). See `jamaendo/api.py` for details.

The code that implements the UI and the rest of the application is licensed under a GPL v3 license.