.. raw:: html

 <a href="https://github.com/futuregrid/teefaa"
     class="visible-desktop"><img
    style="position: absolute; top: 40px; right: 0; border: 0;"
    src="https://s3.amazonaws.com/github/ribbons/forkme_right_gray_6d6d6d.png"
    alt="Fork me on GitHub"></a>


Module Name: system
====================

system.power
------------
Utility for turn on, off and check status of power.

Check status::

    fab system.power:[hostname],status

Output::

    [hostname]
    -------------------------------------------------
    Chassis Power is [on/off]

Turn on the power::

    fab system.power:[hostname],on

Turn off the power::

    fab system.power:[hostname],off


