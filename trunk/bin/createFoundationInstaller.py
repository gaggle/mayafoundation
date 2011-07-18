#!/usr/bin/python

import re
import os

# Instantiate logger class
import logging
if __name__ == "__main__":
	L = logging.getLogger( os.path.basename(__file__) )
	ch = logging.StreamHandler()
	ch.setFormatter( logging.Formatter("%(name)s : %(levelname)s : %(message)s") )
	L.addHandler(ch)
else: L = logging.getLogger( __name__ )
L.setLevel(logging.INFO)

def createFoundationInstaller():
	root = getOneDirUp( os.path.dirname(__file__) )
	dst = os.path.join(root, "release", "foundation_installer.mel")
	payload_path = os.path.join(root, "foundation_installer", "foundation_installer.py")
	template_path = os.path.join(root, "foundation_installer", "foundation_mel_template.mel")

	payload = getFileContent(payload_path)
	template = getFileContent(template_path)
	replaceFilter = "-%replacewithcontent%-";

	content = template.replace( replaceFilter, escape(payload) )
	setFileContent(dst, content)

def getFileContent(path):
	"""Return content of file"""
	f = open(path, "r")
	try:
		content = f.read()
	except:
		raise
	else:
		L.info( "Loaded file '%s'" % path )
		return content
	finally:
		f.close()

def setFileContent(path, content):
	"""Create file with content"""
	f = open(path, "w")
	try:
		f.write(content)
	except:
		raise
	else:
		L.info( "Wrote file '%s'" % path )
	finally:
		f.close()

def escape(string):
	"""Escape characters that needs escaping in order to become a valid MEL
	string
	"""
	newstring = string
	newstring = newstring.replace('\\', '\\\\')
	newstring = newstring.replace('\"', '\\"')
	newstring = newstring.replace('\n', '\\n')
	newstring = newstring.replace('\t', '\\t')
	return newstring

def getOneDirUp(path):
	return os.path.dirname(path)

if __name__ == "__main__":
	createFoundationInstaller()