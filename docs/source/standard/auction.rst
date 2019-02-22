.. . Kicking page rebuild 2014-10-30 17:00:08
.. include:: defs.hrst

.. index:: Auction, Duration, Value, Guarantee, auctionParameters, Bank Account, Сontracts

.. _Auction:

Auction
=======

Schema
------

:id:
  uuid, auto-generated, read-only

  Internal identifier of object in array.

:auctionID:
  string, auto-generated, read-only

  The auction identifier to refer auction to in "paper" documentation. 

  |ocdsDescription|
  It is included to make the flattened data structure more convenient.
   
:procurementMethodType:
  string, auto-generated, read-only

  Type that defines what type of the procedure is going to be used. Possible values: `reporting`.

:procurementMethodDetails:
  string, optional 

  Parameter that accelerates auction periods. Set *quick, accelerator=1440* as text value for `procurementMethodDetails` for the time frames to be reduced in 1440 times. This mechanism works only on the sandbox.

:submissionMethodDetails:
  string, optional 

  Parameter that works only with mode = "test" and speeds up auction start date. 

  Possible value is quick.

:documents:
  Array of :ref:`documents` objects, optional
 
  |ocdsDescription|
  All documents and attachments related to the auction.

:value:
  :ref:`value`, required

  Initial price of the object to be privatized.

  |ocdsDescription|
  The total estimated value of the procurement.

:guarantee:
  :ref:`Guarantee`, required

  Bid guarantee. `Lots.auctions.guaran`

:bankAccount:
  :ref:`bankAccount`, required

  Details which uniquely identify a bank account, and are used when making or receiving a payment.
  
:status: 
  string, required

  Auction status within which the lot is being sold:

+---------------+-------------------------------------------------------+
|    Status     |                    Description                        |
+===============+=======================================================+
| `scheduled`   | The process is planned, but is not yet taking place.  |
+---------------+-------------------------------------------------------+
| `active`      | The process is currently taking place                 |
+---------------+-------------------------------------------------------+
| `complete`    | The process is complete;                              |
+---------------+-------------------------------------------------------+
| `cancelled`   | The process has been cancelled;                       |
+---------------+-------------------------------------------------------+
| `unsuccessful`| The process has been unsuccessful.                    |
+---------------+-------------------------------------------------------+

:contracts:
  Array of :ref:`contracts`, auto-generated, read-only

  Information of the related contract.

:relatedProcessID:
  uuid, required

  Internal id of the procedure.

.. _duration:

Duration
========

Duration in `ISO 8601 <https://en.wikipedia.org/wiki/ISO_8601#Durations>`_.

.. _value:

Value
=====

Schema
------

:amount:    
  float, required

  Should be positive.

  |ocdsDescription|
  Amount as a number.
    
:currency:
  string, required
    
  |ocdsDescription|
  The currency in 3-letter ISO 4217 format.
    
:valueAddedTaxIncluded:
  bool, required

  Possible values are `true` or `false`.

.. _guarantee:

Guarantee
=========

Schema
------

:amount:    
  float, required

  Should be positive.

  |ocdsDescription|
  Amount as a number.
    
:currency:
  string, required
    
  |ocdsDescription|
  The currency in 3-letter ISO 4217 format.

.. _bankAccount:

Bank Account
============

Schema
------

:description:
  string, multilingual, optional
    
  Additional information that has to be noted from the Organizator's point.

:bankName:
  string, required

  Name of the bank.

:accountIdentification:
  Array of :ref:`Classification`, required

  Major data on the account details of the state entity selling a lot, to facilitate payments at the end of the process.

  Most frequently used are:

  * `UA-EDR`; 
  * `UA-MFO`;
  * `accountNumber`.

.. _contracts:

Сontracts
=========

Schema
------

:type:
  string, required, auto-generated, read-only

  Type of the contract. The only value is `yoke`.

:contractID:
  string, required, auto-generated, read-only

  The contract identifier to refer to in “paper” documentation.

  Added as long as the contract is being created within the Module of Contracting.

:relatedProcessID:
  uuid, required, auto-generated, read-only

  Internal identifier of the object within the Module of Contracting.

  Added as long as the contract is being created within the Module of Contracting.
