.. . Kicking page rebuild 2014-10-30 17:00:08
.. include:: defs.hrst

.. index:: Lot, Period, Date, Decisions, Contracts

.. _lot:

Lot
===

Schema
------

:id:
    uuid, auto-generated, read-only

    Internal identifier for this lot.

:lotID:
   string, auto-generated, read-only

   The lot identifier to refer that lot to in the `paper` documentation. 

   |ocdsDescription|
   LotID is included to make the flattened data structure more convenient.

:owner:  
    string, auto-generated, read-only

    The entity whom the lot is owned by.

:date:
    string, auto-generated, read-only

    The date of lot creation/undoing.

:title:
    string, multilingual, required

    * Ukrainian by default (required) - Ukrainian title

    * ``title_en`` (English) - English title

    * ``title_ru`` (Russian) - Russian title

    Oprionally can be mentioned in English/Russian.

    Initial data originates from `asset.title`.

:description:
    string, multilingual, required

    |ocdsDescription|
    A description of the goods, services to be provided.

    * Ukrainian by default - Ukrainian decription

    * ``decription_en`` (English) - English decription

    * ``decription_ru`` (Russian) - Russian decription

    Initial data originates from `asset.description`.
    
:dateModified:    
    string, auto-generated, read-only

    |ocdsDescription|
    Date when the lot was last modified.

:status:
    string, required

    The lot status within the Registry.

+-------------------------+---------------------------------------------------+
|        Status           |                  Description                      |
+=========================+===================================================+
| :`draft`:               |  Lot created but not yet available                |
+-------------------------+---------------------------------------------------+
| :`composing`:           |  Attachment of the asset to the lot               |
+-------------------------+---------------------------------------------------+
| :`verification`:        |  Asset availability check                         |
+-------------------------+---------------------------------------------------+
| :`pending`:             |  Editing the lot                                  |
+-------------------------+---------------------------------------------------+
| :`invalid`:             |  If the lot is incorrectly created                |
+-------------------------+---------------------------------------------------+
| :`active.salable`:      |  Expecting the start of the auction               |
+-------------------------+---------------------------------------------------+
| :`pending.deleted`:     |  Separating the asset                             |
+-------------------------+---------------------------------------------------+
| :`deleted`:             |  Delete a lot                                     |
+-------------------------+---------------------------------------------------+
| :`active.auction`:      |  Holding an auction by lot                        |
+-------------------------+---------------------------------------------------+
| :`active.contracting`:  |  Contracting process                              |
+-------------------------+---------------------------------------------------+
| :`pending.sold`:        |  Separating the asset. Lot sold                   |
+-------------------------+---------------------------------------------------+
| :`sold`:                |  Lot sold                                         |
+-------------------------+---------------------------------------------------+
| :`pending.dissolution`: |  Separating the asset                             | 
+-------------------------+---------------------------------------------------+
| :`dissolved`:           |  Dissolution lot                                  |
+-------------------------+---------------------------------------------------+

:relatedProcesses:
    Array of :ref:`relatedProcesses`
    
    Block containing information about the relation to objects beyond the lot.
    
:decisions:
    Array of :ref:`Decisions`, required

    Also include the data from `asset.decisions <http://assetsbounce.api-docs.registry.ea2.openprocurement.io/en/latest/standard/asset.html#decisions>`_.
    
:lotCustodian:

   :ref:`Organization`, required

   An entity managing the lot. Initial data originates from `asset.assetCustodian <http://assetsbounce.api-docs.registry.ea2.openprocurement.io/en/latest/standard/organization.html#organization>`_.

:items:
    Array of :ref:`Items`, required

    Initial data originates from `asset.items <http://assetsbounce.api-docs.registry.ea2.openprocurement.io/en/latest/standard/item.html>`_.

:lotHolder:
   :ref:`Organization`, required

   Initial data originates from `asset.assetHolder <http://assetsbounce.api-docs.registry.ea2.openprocurement.io/en/latest/standard/organization.html#organization>`_.

:rectificationPeriod:
    :ref:`Period`, auto-generated, read-only

    Period during which the lot's owner can edit it.

:auctions:
    Array of :ref:`Auction`, required

    Auction conditions due to which the lot is to be sold.
    
:documents:
    Array of :ref:`documents` objects
 
    |ocdsDescription|
    All documents and attachments related to the lot.

:mode:
    string, optional

    The additional parameter with a value `test`.

:sandboxParameters:
    string, optional

    Parameter that accelerates lot periods. Set quick, accelerator=1440 as text value for `sandboxParameters` for the time frames to be reduced in 1440 times.

:lotType:
    string, auto-generated, read-only

    Type of the given lot. Given value:

    * `yoke` - lotType for the small scale privatization process.

.. _period:    

Period
======

Schema
------

:startDate:
    string, :ref:`Date`

    |ocdsDescription|
    The start date for the period.
    `startDate` should always precede `endDate`.

:endDate:
    string, :ref:`Date`

    |ocdsDescription|
    The end date for the period.

.. _date:

Date
====

Date/time in `ISO 8601 <https://en.wikipedia.org/wiki/ISO_8601#Dates>`_.


.. _value:

Value
=====

Schema
------

:amount:    
    float, required

    Should be positive.
    
:currency:
    string, required
    
    |ocdsDescription|
    The currency in 3-letter ISO 4217 format.
    
:valueAddedTaxIncluded:
    bool, required

    Possible values are `true` or `false`.


.. _decisions:

Decisions
=========

Schema
------

:title:
    string, multilingual, optional
    
    * Ukrainian by default (optional) - Ukrainian title
    
    * ``title_en`` (English) - English title
    
    * ``title_ru`` (Russian) - Russian title

:decisionDate:
    :ref:`Date`, required

    |ocdsDescription|
    The date on which the document was first published.

:decisionID:
    string, required

    The decision identifier to refer to in the `paper` documentation.

:decisionOf:
    string, required

    Possible values are:

    * `lot`
    * `asset`

:relatedItem:
    string, auto-generated

    Internal id of related asset.


.. _contracts:

Сontracts
=========

Schema
------

:type:
  string, auto-generated, read-only

  Type of the contract. The only value is `yoke`.

:id:
  uuid, auto-generated, read-only

  Internal identifier of the object within the Module of Contracting.

  Added as long as the contract is being created within the Module of Contracting.

:status:
  string, auto-generated, read-only

  Status of contract within the Module of Contracting.

  Added as long as the contract is being created within the Module of Contracting.
