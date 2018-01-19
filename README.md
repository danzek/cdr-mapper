# CDR Mapper [![No Maintenance Intended](http://unmaintained.tech/badge.svg)](http://unmaintained.tech/)

An application that plots towers from call detail record (CDR) data to a map file (kml). It can be used to assist users conducting historical cell site and sector analysis.

Currently it accepts CDR data where the cell sites / towers and CDRs are provided in separate files or where they are in the same row, but where the cell site identifiers are unique to a single network element. See 'future goals' for expansion plans for additional types of data.

This branch uses `easy_gui v0.97` to provide a simple GUI interface. [The master branch](https://github.com/danzek/cdr-mapper/tree/master) is a Flask web application.

I have uploaded [a Windows installer](https://github.com/danzek/cdr-mapper/tree/gui/installer) for the GUI branch.

## License

[MIT](https://github.com/danzek/cdr-mapper/blob/master/LICENSE), Copyright &copy; 2015 Dan O'Day
