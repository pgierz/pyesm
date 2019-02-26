"""
An interface to SQLite Databases to store Model components, experiments,
analyses, etc...

----
"""
import logging
import os
import sqlite3

class ESMDatabase(object):
    """
    A Database to hold your simulations. This may be of interest if you need a
    automatic way to keep track of:

    * Which components your model was composed of

    A SQL database is created at the file defined by the environmental variable
    ``$ESM_DB_PATH``, otherwise the database object is created in memory.
    """

    def __init__(self):
        self.DatabasePath = os.environ.get("ESM_DB_PATH", ":memory:")
        self.connection = sqlite3.connect(self.DatabasePath)
        self.cursor = self.connection.cursor()

    def register_component(self, Name, Version, LateralResolution, VerticalResolution, Timestep):
        """
        Registers the component in the database table `Component`. The record
        takes the form of:

        +--------------+---------------+--------------+-------------+--------------+----------+
        | Component_ID | Name          | Version      | Lateral_Res | Vertical_Res | Timestep |
        +--------------+---------------+--------------+-------------+--------------+----------+
        | 1            | ``Component`` | ``0.0.0``    | ``None``    | ``None``     | ``None`` |
        +--------------+---------------+--------------+-------------+--------------+----------+
        | 2            | ``ECHAM6``    | ``6.3.02p4`` | ``T63``     | ``L47``      | ``450``  |
        +--------------+---------------+--------------+-------------+--------------+----------+

        Parameters
        ----------
        Name : str
            The name of the component to register in the database
        Version : str
            The version of the component
        LateralResolution : str
            The x/y resolution, or name describing it, e.g. T63, T255, 20km
        VerticalResolution : str
            The z resolution
        Timestep : str
            The timestep, ideally with units
        """
        create_table_command = """CREATE TABLE IF NOT EXISTS "Component" ( `Component_ID` INTEGER, `Name` TEXT, `Version` INTEGER, `Lateral_Res` TEXT, `Vertical_Res` TEXT, `Timestep` INTEGER, PRIMARY KEY(`Component_ID`) )"""
        insert_component_command = """INSERT INTO Component (Name, Version, Lateral_Res, Vertical_Res, Timestep) VALUES ("%s", "%s", "%s", "%s", "%s");""" % (str(Name), str(Version), str(LateralResolution),
                                                                                                                                                              str(VerticalResolution), str(Timestep))

        logging.debug(create_table_command)
        logging.debug(insert_component_command)

        self.cursor.execute(create_table_command)
        self.cursor.execute(insert_component_command)
        self.connection.commit()
