#!/usr/bin/env python3
# MIT License
#
# Copyright (c) 2020 FABRIC Testbed
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
#
# Author: Komal Thareja (kthare10@renci.org)

from sqlalchemy import JSON, ForeignKey, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, Sequence

Base = declarative_base()


class Actors(Base):
    """
    Represents Actors Database Table
    """
    __tablename__ = 'Actors'
    act_id = Column(Integer, Sequence('act_id', start=1, increment=1), autoincrement=True, primary_key=True)
    act_name = Column(String, unique=True, nullable=False)
    act_guid = Column(String, nullable=False)
    act_type = Column(Integer, nullable=False)
    properties = Column(LargeBinary)


class Clients(Base):
    """
    Represents Clients Database Table
    """
    __tablename__ = 'Clients'
    clt_id = Column(Integer, Sequence('clt_id', start=1, increment=1), autoincrement=True, primary_key=True)
    clt_act_id = Column(Integer, ForeignKey('Actors.act_id'))
    clt_name = Column(String, nullable=False)
    clt_guid = Column(String, nullable=False)
    properties = Column(LargeBinary)


class ConfigMappings(Base):
    """
    Represents ConfigMappings Database Table
    """
    __tablename__ = 'ConfigMappings'
    cfgm_id = Column(Integer, Sequence('cfgm_id', start=1, increment=1), autoincrement=True, primary_key=True)
    cfgm_act_id = Column(Integer, ForeignKey('Actors.act_id'))
    cfgm_type = Column(String, nullable=False)
    cfgm_path = Column(String, nullable=False)
    properties = Column(JSON)


class ManagerObjects(Base):
    """
    Represents ManagerObjects Database Table
    """
    __tablename__ = 'ManagerObjects'
    mo_id = Column(Integer, Sequence('mo_id', start=1, increment=1), autoincrement=True, primary_key=True)
    mo_key = Column(String, nullable=False, unique=True)
    mo_act_id = Column(Integer, ForeignKey('Actors.act_id'))
    properties = Column(JSON)


class Miscellaneous(Base):
    """
    Represents Miscellaneous Database Table
    """
    __tablename__ = 'Miscellaneous'
    msc_id = Column(Integer, Sequence('msc_id', start=1, increment=1), autoincrement=True, primary_key=True)
    msc_path = Column(String, nullable=False, unique=True)
    properties = Column(JSON)


class Proxies(Base):
    """
    Represents Proxies Database Table
    """
    __tablename__ = 'Proxies'
    prx_id = Column(Integer, Sequence('prx_id', start=1, increment=1), autoincrement=True, primary_key=True)
    prx_act_id = Column(Integer, ForeignKey('Actors.act_id'))
    prx_name = Column(String)
    properties = Column(LargeBinary)


class Reservations(Base):
    """
    Represents Reservations Database Table
    """
    __tablename__ = 'Reservations'
    rsv_id = Column(Integer, Sequence('rsv_id', start=1, increment=1), autoincrement=True, primary_key=True)
    rsv_graph_id = Column(String, nullable=True)
    rsv_slc_id = Column(Integer, ForeignKey('Slices.slc_id'))
    rsv_resid = Column(String, nullable=False)
    rsv_category = Column(Integer, nullable=False)
    rsv_state = Column(Integer, nullable=False)
    rsv_pending = Column(Integer, nullable=False)
    rsv_joining = Column(Integer, nullable=False)
    properties = Column(LargeBinary)


class Slices(Base):
    """
    Represents Slices Database Table
    """
    __tablename__ = 'Slices'
    slc_id = Column(Integer, Sequence('slc_id', start=1, increment=1), autoincrement=True, primary_key=True)
    slc_graph_id = Column(String, nullable=True)
    slc_guid = Column(String, nullable=False)
    slc_name = Column(String, nullable=False)
    slc_type = Column(Integer, nullable=False)
    slc_act_id = Column(Integer, ForeignKey('Actors.act_id'))
    slc_resource_type = Column(String)
    properties = Column(LargeBinary)


class Units(Base):
    """
    Represents Units Database Table
    """
    __tablename__ = 'Units'
    unt_id = Column(Integer, Sequence('unt_id', start=1, increment=1), autoincrement=True, primary_key=True)
    unt_uid = Column(String)
    unt_unt_id = Column(Integer, nullable=True)
    unt_act_id = Column(Integer, ForeignKey('Actors.act_id'))
    unt_slc_id = Column(Integer, ForeignKey('Slices.slc_id'))
    unt_rsv_id = Column(Integer, ForeignKey('Reservations.rsv_id'))
    unt_type = Column(Integer, nullable=False)
    unt_state = Column(Integer, nullable=False)
    properties = Column(LargeBinary)


class Plugins(Base):
    """
    Represents Plugins Database Table
    """
    __tablename__ = 'Plugins'
    plg_id = Column(Integer, Sequence('plg_id', start=1, increment=1), autoincrement=True, primary_key=True)
    plg_local_id = Column(String, nullable=False)
    plg_type = Column(Integer, nullable=False)
    plg_actor_type = Column(Integer)
    properties = Column(LargeBinary)


class Delegations(Base):
    """
    Represents Delegations Database Table
    """
    __tablename__ = 'Delegations'
    dlg_id = Column(Integer, Sequence('dlg_id', start=1, increment=1), autoincrement=True, primary_key=True)
    dlg_slc_id = Column(Integer, ForeignKey('Slices.slc_id'))
    dlg_act_id = Column(Integer, ForeignKey('Actors.act_id'))
    dlg_graph_id = Column(String, nullable=False)
    dlg_state = Column(Integer, nullable=False)
    properties = Column(LargeBinary)
