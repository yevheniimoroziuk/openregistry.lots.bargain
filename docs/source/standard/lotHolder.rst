.. . Kicking page rebuild 2014-10-30 17:00:08
.. include:: defs.hrst

.. index:: Organization, Company

.. _lotHolder:

Lot Holder
============

Schema
------

:name:
    string, multilingual, required
    
    Name of the entity.
    
:identifier:
    :ref:`Identifier`, required
    
    The primary identifier for this entity. 
    
:additionalIdentifiers:
    Array of :ref:`identifier` objects
    
:address:
    :ref:`address`, optional
    
:contactPoint:
    :ref:`contactPoint`, optional

:additionalContactPoints:
    Array of :ref:`contactPoint`, optional
