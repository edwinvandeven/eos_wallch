#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import dbus
import os
import configparser
import getpass
import sys
from gi.repository import Gio
from pathlib import Path
from shutil import copyfile
from time import sleep


CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".config", "eos_wallch", "config.ini")
CONFIG = configparser.ConfigParser()
CONFIG.read(CONFIG_PATH)


def _get_dark_mode_active():
    gso = Gio.Settings.new("org.freedesktop")
    option = "prefers-color-scheme"

    value = str(gso.get_value(option))
    dark_mode_active = False
    if value == "'dark'":
        dark_mode_active = True
        
    return dark_mode_active
    
def _get_current_wallpaper():
    gso = Gio.Settings.new("org.gnome.desktop.background")
    return str(gso.get_value("picture-uri"))

def _parse_args():
    parser = argparse.ArgumentParser(description='Elementary Night wallpaper switcher.')
    # parser.add_argument('--set', help='use "set" as the first argument to store the current wallpaper')
    parser.add_argument("-s", "--set",
                        action="store_true", 
                        help="Set current wallpaper as day or night wallpaper")
    args = parser.parse_args()
    
    return args
    
def _set():
    dark_mode_active = _get_dark_mode_active()
    picture_uri = _get_current_wallpaper()
    if not dark_mode_active:
        print("Light wallpaper set to: %s" % picture_uri)
        CONFIG['light']['picture_uri'] = picture_uri
    else:
        print("Dark wallpaper set to: %s" % picture_uri)
        CONFIG['dark']['picture_uri'] =  picture_uri
        
    with open (CONFIG_PATH, "w") as config_file:
        CONFIG.write(config_file)
        
    sys.exit()
        
def _update_wallpaper(picture_uri):
    picture_uri = picture_uri.replace("'", '')
    # Update gsettings value
    gso = Gio.Settings.new("org.gnome.desktop.background")
    gso.set_string("picture-uri", picture_uri)
    
    # Copy to /var/lib/lightdm-data/<username>/wallpaper/
    username = getpass.getuser()
    lightdm_wall_folder = "/var/lib/lightdm-data/%s/wallpaper" % username
    wall_source_path = picture_uri.replace("file://", "")
    lightdm_dest = os.path.join(lightdm_wall_folder, os.path.basename(wall_source_path))
    
    # Clean up folder before copy
    [f.unlink() for f in Path(lightdm_wall_folder).glob("*") if f.is_file()]    
    copyfile(wall_source_path, lightdm_dest)
    
    # Set greeter image
    system_bus = dbus.SystemBus()
    uid = os.getuid()
    obj_path = "/org/freedesktop/Accounts/User%s" % str(uid)
    print(obj_path)    
    system_bus = dbus.SystemBus()
    proxy = system_bus.get_object("org.freedesktop.Accounts", obj_path)
    properties_manager = dbus.Interface(proxy, 'org.freedesktop.DBus.Properties')
    properties_manager.Set('org.freedesktop.DisplayManager.AccountsService', 'BackgroundFile', lightdm_dest)
    
    
def _keep_wallpaper_in_sync():
    dark_mode_active = _get_dark_mode_active()
    current_wallpaper = _get_current_wallpaper()
    if dark_mode_active:
        # Dark mode
        dark_wallpaper = CONFIG['dark']['picture_uri']
        if current_wallpaper != dark_wallpaper:
            _update_wallpaper(dark_wallpaper)
    else:
        # Light mode
        light_wallpaper = CONFIG['light']['picture_uri']
        if current_wallpaper != light_wallpaper:
            _update_wallpaper(light_wallpaper)
    
    sleep(120)
    _keep_wallpaper_in_sync()

def main():    
    args = _parse_args()
    if args.set:
        _set()
        
    _keep_wallpaper_in_sync()

if __name__ == "__main__":
    main()
