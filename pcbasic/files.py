"""
PC-BASIC - files.py
Devices, Files and I/O operations

(c) 2013, 2014, 2015, 2016 Rob Hagemans
This file is released under the GNU GPL version 3 or later.
"""

import string
import os
import logging

import error
import devices
import cassette
import disk
import ports

import state
import config

import plat
if plat.system == b'Windows':
    import win32api

# MS-DOS device files
device_files = ('AUX', 'CON', 'NUL', 'PRN')

############################################################################
# General file manipulation

class Files(object):
    """ File manager. """

    def __init__(self, devices, max_files):
        """ Initialise files. """
        self.files = {}
        self.max_files = max_files
        self.devices = devices

    def open(self, number, description, filetype, mode='I', access='R', lock='',
                  reclen=128, seg=0, offset=0, length=0):
        """ Open a file on a device specified by description. """
        if (not description) or (number < 0) or (number > self.max_files):
            # bad file number; also for name='', for some reason
            raise error.RunError(error.BAD_FILE_NUMBER)
        if number in self.files:
            raise error.RunError(error.FILE_ALREADY_OPEN)
        name, mode = str(description), mode.upper()
        inst = None
        split_colon = name.split(':')
        if len(split_colon) > 1: # : found
            dev_name = split_colon[0].upper() + ':'
            dev_param = ''.join(split_colon[1:])
            try:
                device = self.devices.devices[dev_name]
            except KeyError:
                # not an allowable device or drive name
                # bad file number, for some reason
                raise error.RunError(error.BAD_FILE_NUMBER)
        else:
            device = state.io_state.current_device
            # MS-DOS device aliases - these can't be names of disk files
            if device != self.devices.devices['CAS1:'] and name in device_files:
                if name == 'AUX':
                    device, dev_param = self.devices.devices['COM1:'], ''
                elif name == 'CON' and mode == 'I':
                    device, dev_param = self.devices.devices['KYBD:'], ''
                elif name == 'CON' and mode == 'O':
                    device, dev_param = self.devices.devices['SCRN:'], ''
                elif name == 'PRN':
                    device, dev_param = self.devices.devices['LPT1:'], ''
                elif name == 'NUL':
                    device, dev_param = devices.NullDevice(), ''
            else:
                # open file on default device
                dev_param = name
        # open the file on the device
        new_file = device.open(number, dev_param, filetype, mode, access, lock,
                               reclen, seg, offset, length)
        if number:
            self.files[number] = new_file
        return new_file

    def get(self, num, mode='IOAR'):
        """ Get the file object for a file number and check allowed mode. """
        try:
            the_file = self.files[num]
        except KeyError:
            raise error.RunError(error.BAD_FILE_NUMBER)
        if the_file.mode.upper() not in mode:
            raise error.RunError(error.BAD_FILE_MODE)
        return the_file

    def close(self, num):
        """ Close a numbered file. """
        try:
            self.files[num].close()
            del self.files[num]
        except KeyError:
            pass

    def close_all(self):
        """ Close all files. """
        for f in self.files.values():
            f.close()
        self.files = {}


###############################################################################
# device management

class Devices(object):
    """ Device manager. """

    # allowable drive letters in GW-BASIC are letters or @
    drive_letters = b'@' + string.ascii_uppercase

    def __init__(self):
        """ Initialise devices. """
        self.devices = {}
        # console
        self.devices['SCRN:'] = devices.SCRNDevice()
        self.devices['KYBD:'] = devices.KYBDDevice()
        state.io_state.scrn_file = self.devices['SCRN:'].device_file
        state.io_state.kybd_file = self.devices['KYBD:'].device_file
        # ports
        # parallel devices - LPT1: must always be defined
        print_trigger = config.get('print-trigger')
        self.devices['LPT1:'] = ports.LPTDevice(config.get('lpt1'), devices.nullstream(), print_trigger)
        self.devices['LPT2:'] = ports.LPTDevice(config.get('lpt2'), None, print_trigger)
        self.devices['LPT3:'] = ports.LPTDevice(config.get('lpt3'), None, print_trigger)
        state.io_state.lpt1_file = self.devices['LPT1:'].device_file
        # serial devices
        # buffer sizes (/c switch in GW-BASIC)
        serial_in_size = config.get('serial-buffer-size')
        self.devices['COM1:'] = ports.COMDevice(config.get('com1'), serial_in_size)
        self.devices['COM2:'] = ports.COMDevice(config.get('com2'), serial_in_size)
        # cassette
        self.devices['CAS1:'] = cassette.CASDevice(config.get('cas1'))
        # disk devices
        for letter in self.drive_letters:
            self.devices[letter + b':'] = disk.DiskDevice(letter, None, u'')
        current_drive = config.get(u'current-device').upper()
        if config.get(u'map-drives'):
            current_drive = self._map_drives()
        else:
            self.devices[b'Z:'] = disk.DiskDevice(b'Z', os.getcwdu(), u'')
        self._mount_drives(config.get(u'mount'))
        self._set_current_device(current_drive + b':')


    def _mount_drives(self, mount_list):
        """ Mount disk drives """
        if not mount_list:
            return
        for a in mount_list:
            # the last one that's specified will stick
            try:
                letter, path = a.split(u':', 1)
                letter = letter.encode(b'ascii', errors=b'replace').upper()
                path = os.path.realpath(path)
                if not os.path.isdir(path):
                    logging.warning(u'Could not mount %s', a)
                else:
                    self.devices[letter + b':'] = disk.DiskDevice(letter, path, u'')
            except (TypeError, ValueError) as e:
                logging.warning(u'Could not mount %s: %s', a, unicode(e))


    def _set_current_device(self, current_drive, default=b'Z:'):
        """ Set the current device. """
        try:
            state.io_state.current_device = self.devices[current_drive]
        except KeyError:
            logging.warning(u'Could not set current device to %s', current_drive)
            state.io_state.current_device = self.devices[default]


    if plat.system == b'Windows':
        def _map_drives(self):
            """ Map Windows drive letters to PC-BASIC disk devices. """
            # get all drives in use by windows
            # if started from CMD.EXE, get the 'current working dir' for each drive
            # if not in CMD.EXE, there's only one cwd
            current_drive = os.path.abspath(os.getcwdu()).split(u':')[0].encode('ascii')
            save_current = os.getcwdu()
            drives = {}
            for letter in win32api.GetLogicalDriveStrings().split(u':\\\0')[:-1]:
                try:
                    os.chdir(letter + u':')
                    cwd = win32api.GetShortPathName(os.getcwdu())
                except Exception:
                    # something went wrong, do not mount this drive
                    # this is often a pywintypes.error rather than a WindowsError
                    pass
                else:
                    # must not start with \\
                    path, cwd = cwd[:3], cwd[3:]
                    bletter = letter.encode(b'ascii')
                    self.devices[bletter + b':'] = disk.DiskDevice(bletter, path, cwd)
            os.chdir(save_current)
            return current_drive
    else:
        def _map_drives(self):
            """ Map useful Unix directories to PC-BASIC disk devices. """
            cwd = os.getcwdu()
            # map C to root
            self.devices[b'C:'] = disk.DiskDevice(b'C', u'/', cwd[1:])
            # map Z to cwd
            self.devices[b'Z:'] = disk.DiskDevice(b'Z', cwd, u'')
            # map H to home
            home = os.path.expanduser(u'~')
            # if cwd is in home tree, set it also on H:
            if cwd[:len(home)] == home:
                self.devices[b'H:'] = disk.DiskDevice(b'H', home, cwd[len(home)+1:])
            else:
                self.devices[b'H:'] = disk.DiskDevice(b'H', home, u'')
            # default durrent drive
            return b'Z'

    def close(self):
        """ Close device master files. """
        for d in self.devices.values():
            d.close()
