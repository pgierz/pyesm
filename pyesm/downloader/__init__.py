"""
Downloads various ESM components from repositories

Provides pythonic interfaces to download models from git, svn, ect...

----
"""
import os
import shutil
import subprocess

try:
    import git
    git_module_available = True
except ImportError:
    git_module_available = False

# TODO: How to override this from the outside?
FancyDisplay = False

if FancyDisplay:
    if git_module_available:
        try:
            import emoji
            UseEmoji = True
        except ImportError:
            print("Fancy display might not work for everything...")
            UseEmoji = False
        try:
            import tqdm
        except ImportError:
            print("Fancy display doesn't work at all, sorry!")
            FancyDisplay = False
else:
    print("Fancy display doesn't work at all, sorry!")

def download_from_git(GitAddress, DestPath, ModelName, ModelType):
    """Downloads a git repository to a specific path.

    Arguments
    ---------
    GitAddress : str
        The full location to the repo you want to clone
    DestPath : str
        The full location of the destination where the repo should go
    ModelName : str
        The Name of the model, for printing output
    ModelType : str
        What kind of model is being downloaded (atmoshpere, land, ocean, etc...)


    Example
    -------
    >>> download_from_git("https://gitlab.dkrz.de/modular_esm/echam6.git", "echam6", "ECHAM6", "Atmoshpere")
    """
    _num_op_codes = 9
    BEGIN, END, COUNTING, COMPRESSING, WRITING, RECEIVING, RESOLVING, FINDING_SOURCES, CHECKING_OUT = \
            [1 << x for x in range(_num_op_codes)]
    phases = {BEGIN: "BEGIN", END: "END", 
              COUNTING+BEGIN:           "COUNTING BEGIN",           COUNTING:        "COUNTING",               COUNTING+END: "COUNTING END",
              COMPRESSING+BEGIN:        "COMPRESSING BEGIN",        COMPRESSING:     "COMPRESSING",         COMPRESSING+END: "COMPRESSING END",
              WRITING+BEGIN:            "WRITING BEGIN",            WRITING:         "WRITING",                 WRITING+END: "WRITING END",
              RECEIVING+BEGIN:          "RECEIVING BEGIN",          RECEIVING:       "RECEIVING",             RECEIVING+END: "RECEIVING END",
              RESOLVING+BEGIN:          "RESOLVING BEGIN",          RESOLVING:       "RESOLVING",             RESOLVING+END: "RESOLVING END",
              FINDING_SOURCES+BEGIN:    "FINDING_SOURCES BEGIN",    FINDING_SOURCES: "FINDING_SOURCES", FINDING_SOURCES+END: "FINDING_SOURCES END",
              CHECKING_OUT+BEGIN:       "CHECKING_OUT BEGIN",       CHECKING_OUT:    "CHECKING_OUT",       CHECKING_OUT+END: "CHECKING_OUT END"}

    def my_hook(t):
        last_b = [0]
        def update_to(op_code, b=1, tsize=None, msg=None):
            action_phases = [COUNTING, COMPRESSING, WRITING, RECEIVING,
                            RESOLVING, FINDING_SOURCES, CHECKING_OUT]
            if op_code in action_phases:
                t.set_postfix_str(phases[op_code])
                if tsize is not None:
                    t.total = tsize
                t.update((b - last_b[0]))
                last_b[0] = b
            if op_code in [END + action for action in action_phases]:
                t.clear()
                last_b[0] = 0
        return update_to

    if UseEmoji:
        type_to_emoji = {"Atmosphere": ":cloud:", "Land": ":seedling:",
                         "Ocean": ":ocean:", "Ice": ":snowflake:", 
                         "Solid Earth": ":comet:", "Coupler": ":link:"}

        EmojiString = emoji.emojize(type_to_emoji.get(ModelType, ":puzzle:"))
    else:
        EmojiString = ""

    if FancyDisplay:
        with tqdm.tqdm(ncols=120, desc=emoji.emojize("Cloning "+ModelName+" "+EmojiString)) as t:
            dl_hook = my_hook(t)
            git.Repo.clone_from(GitAddress, to_path=DestPath, progress=dl_hook)
    else:
        print("Cloning %s Model %s" % (ModelType, ModelType))
        if git_module_available:
            git.Repo.clone_from(GitAddress, to_path=DestPath)
        else:
            subprocess.check_output([GitAddress, DestPath])
