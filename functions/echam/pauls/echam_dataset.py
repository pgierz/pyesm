import os

from ruamel.yaml import YAML, yaml_object

yaml = YAML()


def check_year(year, start_valid, end_valid):
    """ Checks if a year is within a valid range.

    Parameters
    ----------
    year : int
        The year to check
    start_valid : int
        The minimum bound for validity of a specific year.
    end_valid: int
        The maximum bound for vaility of a specific year

    Returns
    -------
        bool
            True or False depending on if the year is valid or not.
    """
    return (start_valid <= year) and (year <= end_valid)


# NOTE: Please inherit from object until we switch fully to python >= 3
@yaml_object(yaml)
class Dataset(object):
    """
    Describes a released ``ECHAM6`` dataset.

    A ``Dataset`` object describes the set of files that are used for input,
    forcing, etc. for a specific version of ``ECHAM6``. While the base class
    doesn't define any files, there are methods defined here which are used to
    sort files according to specific years for which they are valid, and for
    finding a "class" for files; e.g.:
        + input files
        + forcing files
        + ...
    """
    # The keys here would correspond to filepaths, the values are a dictionary
    # of "from": minimum valid year, "to": maximum valid year
    example_fileset = {
        "big_bang": {"from": float('-inf'), "to": 2016},
        "Trump_Time_and_Sadness": {"from": 2016, "to": 2020},
        "The_Future_at_@YEAR@": {"from": 2020, "to": float('inf')}
        }


    def find(self, filetype, year):
        """
        Finds files for a filetype for a given year.

        Searches through the Dataset's attribute attached to ``filetype`` and
        retrieves all files for the appropriate year. The returned filename
        will have any substring @YEAR@ replaced by a string representation of
        the argument ``year``.

        Parameters
        ----------
            filetype : str
                The ``filetype`` parameter is used to get the dictionary of files
                to check through.
            year : int
                The ``year`` parameter is used to check the validity of a
                specific file, and is **also** used in replacement of a special
                string @YEAR@.

        Yields
        ------
            tuple of (str, str)
                A tuple of strings corresponding to the human readable name of
                the file, and the appropriate file to use, where the year has
                been inserted.
        """
        # NOTE: If you don't know what generators are, have a look here:
        # https://realpython.com/introduction-to-python-generators/
        filetype_dict = getattr(self, filetype)
        for human_readable_name, file_dict in filetype_dict.items():
            for key, value in file_dict.items():
                if check_year(year, value["from"], value["to"]):
                    yield human_readable_name, key.replace("@YEAR@", str(year))


@yaml_object(yaml)
class EchamRestart(Dataset):
    def __init__(self, basedir, parentexpid, parentdate):
        self.parentexpid = parentexpid
        self.parentdate = parentdate
        self.basedir = basedir

        unallowed_streams = ["jsbach", "jsbid", "veg", "yasso", "surf", "hd"]

        filelist = os.listdir(basedir+"/restart_"+self.parentexpid+"_"+self.parentdate+"_*.nc")
        for file in filelist:
            stream = os.path.basename(file).split("_")[-2]
            if stream not in unallowed_streams:
                setattr(self, stream,
                        "/restart_"+self.parentexpid+"_"+self.parentdate+"_"+stream+".nc")


@yaml_object(yaml)
class r0007(Dataset):
    """ A description of the r0007 Dataset with input and forcing data for ``ECHAM6``"""
    def __init__(self, res, levels, oceres):
        self.res = res
        self.levels = levels
        self.oceres = oceres

        self.input_in_pool = {
        }


        }

        self.forcing_in_pool = {
        }
