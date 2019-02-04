.. . Kicking page rebuild 2014-10-30 17:00:08
.. include:: defs.hrst

.. index:: relatedProcesses

.. _relatedProcesses:

Related Processes
=================

Schema
------

:id:
    uuid, auto-generated, read-only

    Internal identifier for this related process.

:type:
    string, required

    Type of this related process. The only value is `asset`. 

:relatedProcessID:
    uuid, required

    Internal identifier for asset.

:identifier:
    string, auto-generated, read-only

    The asset identifier to refer to in the `paper` documentation.

   |ocdsDescription|
   `AssetID` is included to make the flattened data structure more convenient.
