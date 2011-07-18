#!/usr/bin/env python
#
# foundation_installer.py
# mayaPyTools
"""NOTE: Upon module load the Foundation installer is automatically initialized!

This is done to ease the initialization of the installer because it shifts the
code completely into Python domain instead of relying on fickle MEL to get
started"""

from collections import defaultdict
import webbrowser
import datetime
import os.path
import sys
import re
import maya.cmds as mc
import maya.mel
import traceback


# Instantiate logger class
import logging
L = logging.getLogger( __name__ )
L.setLevel(logging.ERROR)
#if not L.handlers:
#	ch = logging.StreamHandler()
#	ch.setFormatter( logging.Formatter("%(name)s : %(levelname)s : %(message)s") )
#	L.addHandler(ch)


# Custom exceptions
class FoundationException(Exception):
	def __init__(self, value): self.value = value
	def __str__(self): return repr(self.value)

class UnknownPlatformException(FoundationException):
	def __init__(self): self.value = "Could not detect platform"
	def __str__(self): return repr(self.value)


class Observable(defaultdict):
	"""Observer class designed for lightweight messaging."""
	def __init__ (self):
		defaultdict.__init__(self, object)

	def emit (self, *args):
		'''Pass parameters to all observers and update states.'''
		topic = args[0]
		for subscriber in self:
			if not self[subscriber] or self[subscriber] == topic:
				try:
					response = subscriber(*args)
					L.debug( "Emitted message '%s' to '%s'" % (
						args, subscriber
					) )
				except:
					L.error( "Exception while emitting message '%s' to '%s'" % (
						args, subscriber
					) )
					raise

	def subscribe (self, subscriber, filter=None):
		'''Add a new subscriber to self.'''
		self[subscriber] = filter
obs = Observable()

class View(object):

	def __init__(self):
		self.prefs = self.Preferences()

		# Create our window
		self.window = self._createWindow()
		self.baseForm = self._createBaseForm()

		self.leftForm = self._createLeftForm(self.baseForm)
		self.steps = self.Steps(
			self,
			self.leftForm
		)

		self.rightForm = self._createRightForm(self.baseForm, self.leftForm)

		self.headline = self.Headline(self.rightForm)

		self.contentBackground = self._createContentBackground(
			self,
			self.rightForm,
			self.headline,
			235,
		)

		self.introductionPanel = self.IntroductionPanel(
			self,
			self.contentBackground,
			self.headline,
		)

		self.selectFolderPanel = self.SelectFolderPanel(
			self,
			self.contentBackground,
			self.headline,
			visible=False,
		)

		self.summaryPanel = self.SummaryPanel(
			self,
			self.contentBackground,
			self.headline,
			visible=False,
		)

		self.buttonGroup = self.ButtonGroup(
			self,
			self.rightForm,
			self.contentBackground,
		)

		mc.showWindow(self.prefs.window)

	class Preferences(object):
		def __init__(self):
			self.platform = getMayaPlatform()
			self.window = "installerWindow"

			# Width of window
			self.width = 532

			# Height of the part with "-shared Python scripting..."
			if self.platform == "mac": self.topHeight = 60
			else: self.topHeight = 50


			self.stageContentBorderSide = 10
			self.stageContentBorderTop = 10
			self.stageContentBorderBottom = 50
			self.stageDescr1to2Separation = 10
			self.stageHeadlineBorderTop = 15
			self.stageBorderBottom = 7
			self.pageBorderTop = 70
			self.pageEntryButtonSeparation = 15

			self.installationStatusHeight = 180

			self.installationStatusColor = [.5,1,.25]
			self.installationStatusShortText = "Install succeeded"
			self.installationStatusLongText = "Awesome! Install succeeded.\n\nPlease restart Maya for changes to take effect. Enjoy."

			self.installationFailedStatusColor = [1,.25,.25]
			self.installationFailedStatusShortText = "Install failed"
			self.installationFailedStatusLongText = "Dammit, Install failed.\n\nSee Installation details for, well, details."

			self.col_dark = [.18,.18,.18]

	def _createWindow(self):
		# If the window already exists we delete it
		if mc.window(self.prefs.window, exists=True):
			mc.deleteUI(self.prefs.window)

		# Remove the window preference, if there is one. We want to make
		# sure the window comes up in its intended size and position.
		if mc.windowPref(self.prefs.window, exists=True):
			mc.windowPref(self.prefs.window, remove=True)
		window = mc.window(
			self.prefs.window,
			title="maya foundation installer",
			sizeable=False,
			minimizeButton=False,
			maximizeButton=False,
			width=self.prefs.width,
		)
		return window

	def closeWindow(self):
		mc.deleteUI(self.prefs.window, window=True)

	def setResizeable(self, bool):
		mc.window(
			self.prefs.window,
			edit=True,
			sizeable=bool,
			maximizeButton=bool,
		)
		mc.window(
			self.prefs.window,
			edit=True,
			width=self.prefs.width + 1,
		)
		mc.window(
			self.prefs.window,
			edit=True,
			width=self.prefs.width,
		)

	def _createBaseForm(self):
		return mc.formLayout()

	def _createLeftForm(self, parent):
		# Left half of main window
		leftHalf = mc.columnLayout(
		)
		mc.formLayout(
			parent,
			edit=True,
			attachForm=[
				(leftHalf, 'top', self.prefs.pageBorderTop),
				(leftHalf, 'left', 5),
				(leftHalf, 'bottom', 5),
			]
		)
		mc.setParent('..')
		return leftHalf

	def _createRightForm(self, parent, leftAlign):
		# Right half of main window
		rightHalf = mc.formLayout(
		)
		mc.formLayout(
			parent,
			edit=True,
			attachForm=[
				(rightHalf, 'top', self.prefs.stageHeadlineBorderTop),
				(rightHalf, 'right', 5),
				(rightHalf, 'bottom', self.prefs.stageBorderBottom),
			],
			attachControl=[
				(rightHalf, 'left', 5, leftAlign),
			]
		)
		mc.setParent('..')
		return rightHalf

	def _createContentBackground(self, owner, control_parent, leftTopAlign, height):
		panel = mc.columnLayout(
			adjustableColumn=2,
			columnOffset=('both', self.prefs.stageContentBorderSide),
			bgc=owner.prefs.col_dark,
			parent=control_parent,
			height=height,
		)
		mc.formLayout(
			control_parent,
			edit=True,
			attachForm=[
				(leftTopAlign, 'left', 5),
				(panel, 'left', 5),
				(panel, 'right', 5),
				(panel, 'bottom', 5),
			],
			attachControl=[
				(panel, 'top', 5, leftTopAlign),
			],
		)
		mc.setParent('..')
		mc.setParent('..')
		return panel

	class Steps(object):
		def __init__(self, owner, control_parent):
			"""Create three pages entries"""

			mc.radioCollection(
				"steps"
			)
			self.intro = owner.StepElement(
				owner,
				control_parent,
				"Introduction",
				enable=True
			)
			self.selectFolder = owner.StepElement(
				owner,
				control_parent,
				"Shared Folder select",
				enable=False
			)
			self.summary = owner.StepElement(
				owner,
				control_parent,
				"Summary",
				enable=False
			)
		def step1(self):
			self.intro.enable()
			self.selectFolder.disable()
			self.summary.disable()
		def step2(self):
			self.intro.disable()
			self.selectFolder.enable()
			self.summary.disable()
		def step3(self):
			self.intro.disable()
			self.selectFolder.disable()
			self.summary.enable()
		def __str__(self):
			return (self.intro, self.selectFolder, self.summary)

	class Headline(object):
		def __init__(self, parent):
			self.headline = mc.text(
				label="Welcome to the maya foundation installer",
				font='boldLabelFont',
				parent=parent,
			)
		def setLabel(self, text):
			mc.text(
				self.headline,
				edit=True,
				label=text,
			)
		def __str__(self):
			return self.headline

	class IntroductionPanel(object):
		def __init__(self, owner, control_parent, setLabel_control, visible=None):
			self.owner = owner
			self.control_parent = control_parent
			self.setLabel_control = setLabel_control

			self.panel = mc.columnLayout(
				adjustableColumn=2,
				columnOffset=('both', owner.prefs.stageContentBorderSide),
				parent=control_parent,
			)
			owner.spacer(owner.prefs.stageContentBorderTop)
			stageDescription1 = mc.text(
				label="maya foundation\n- shared Python scripting environment made easy -",
				font='boldLabelFont',
			)
			owner.spacer(owner.prefs.stageDescr1to2Separation)
			stageDescription = mc.text(
				label="maya foundation streamlines setting up a shared scripting environment for Maya. A shared scripting environment means all Maya installations load the same set of scripts, and that is an essential foundation for developing and maintaining your production tools.\n\nmaya foundation is free, open source, and licensed under the New BSD License meaning you can do with it as you please with no strings attached. For more information see:",
				ww=True,
				font='plainLabelFont',
				align='left',
				width=350,
				height=140,
			)
			self.webbutton = mc.button(
				label="foundation.jonlauridsen.com",
			)
			mc.setParent('..')
			mc.setParent('..')
			mc.setParent('..')

			if visible is not None:
				self.setVisible(visible)

		def setVisible(self, bool):
			mc.layout(self.panel, edit=True, visible=bool)
			if bool:
				self.setLabel_control.setLabel(
					"Welcome to the maya foundation installer"
					)

		def __str__(self):
			return self.panel

	class SelectFolderPanel(object):
		def __init__(self, owner, control_parent, setLabel_control, visible=None):
			self.owner = owner
			self.control_parent = control_parent
			self.setLabel_control = setLabel_control

			self.panel = mc.columnLayout(
				adjustableColumn=2,
				columnOffset=('both', owner.prefs.stageContentBorderSide),
				parent=control_parent,
			)
			owner.spacer(owner.prefs.stageContentBorderTop)
			stageDescription = mc.text(
				label="Select the path where shared scripts reside. This is often a place under version control (within a Perforce depot or an SVN repository) or a folder on a network drive.\n\nIf you're unsure which path to choose please consult your company's help documents, technical art department or network administrator.",
				ww=True,
				font='plainLabelFont',
				align='left',
				width=350,
				height=110,
			)
			owner.spacer(owner.prefs.stageDescr1to2Separation)
			stageDescription1 = mc.text(
				label="Shared Scripting folder:",
				align='left',
				font='boldLabelFont',
			)
			self.sharedFolderButtonGroup = mc.textFieldButtonGrp(
				label="",
				text="",
				buttonLabel='Browse...',
				adjustableColumn=2,
				columnWidth=[1,0],
			)

			owner.spacer(height=6)
			self.noFilesWritten = mc.rowLayout(
				numberOfColumns=2,
				adjustableColumn=2,
				columnWidth2=[16,1],
				visible=False
			)
			mc.text(
				label="*"
			)
			mc.text(
				label="After installation Maya will use the pre-existing file 'sharedUserSetup.py' from this folder.",
				align='left',
				ww=True,
				width=300,
			)

			mc.setParent('..')
			mc.setParent('..')
			mc.setParent('..')
			mc.setParent('..')

			if visible is not None:
				self.setVisible(visible)

		def setVisible(self, bool):
			mc.layout(self.panel, edit=True, visible=bool)
			if bool:
				self.setLabel_control.setLabel(
					"Choosing the Shared Scripting folder"
				)

		def setPathLabel(self, text):
			if text is None:
				text = ""
			mc.textFieldButtonGrp(
				self.sharedFolderButtonGroup,
				edit=True,
				text=text,
			)

		def getPathLabel(self):
			path = mc.textFieldButtonGrp(
				self.sharedFolderButtonGroup,
				query=True,
				text=True,
			)
			return path

		def setNoFilesWrittenVisible(self, bool):
			mc.layout(
				self.noFilesWritten,
				edit=True,
				visible=bool,
			)

		def __str__(self):
			return self.panel

	class SummaryPanel(object):
		def __init__(self, owner, control_parent, setLabel_control, visible=None):
			self.owner = owner
			self.control_parent = control_parent
			self.setLabel_control = setLabel_control

			self.panel = mc.columnLayout(
				adjustableColumn=2,
				columnOffset=('both', owner.prefs.stageContentBorderSide),
				parent=control_parent,
			)
			owner.spacer(owner.prefs.stageContentBorderTop)


			self.installationHeadline = mc.text(
				label=owner.prefs.installationStatusLongText,
				font='boldLabelFont',
				#bgc=owner.prefs.installationStatusColor,
				height=owner.prefs.installationStatusHeight,
			)

			owner.spacer(owner.prefs.stageDescr1to2Separation)

			self.installationFrameLayout = mc.frameLayout(
				label="Installation details",
				collapsable=True,
				collapse=True,
				width=350,
				borderStyle="in",
			)
			mc.setParent('..')
			mc.setParent('..')
			mc.setParent('..')
			mc.setParent('..')

			if visible is not None:
				self.setVisible(visible)

		def setVisible(self, bool):
			mc.layout(self.panel, edit=True, visible=bool)
			if bool:
				self.setLabel_control.setLabel(
					"Installation completed successfully"
				)
		def setPathLabel(self, text):
			if text is None:
				text = ""
			mc.textFieldButtonGrp(
				self.sharedFolderButtonGroup,
				edit=True,
				text=text,
			)
		def getPathLabel(self):
			path = mc.textFieldButtonGrp(
				self.sharedFolderButtonGroup,
				query=True,
				text=True,
			)
			return path

		def setInstallationSuccess(self, success=True):
			if success:
				pass
			else:
				mc.text(
					self.installationHeadline,
					edit=True,
					bgc=self.owner.prefs.installationFailedStatusColor,
				)
				self.setInstallation_short(success=False)
				self.setInstallation_long(success=False)


		def setInstallation_short(self, success=True):
			if success:
				t = self.owner.prefs.installationStatusShortText
			else:
				t = self.owner.prefs.installationFailedStatusShortText


			self._setInstallationHeadline(
				t, 20
			)

		def setInstallation_long(self, success=True):
			if success:
				t = self.owner.prefs.installationStatusLongText
			else:
				t = self.owner.prefs.installationFailedStatusLongText

			self._setInstallationHeadline(
				t, self.owner.prefs.installationStatusHeight
			)

		def _setInstallationHeadline(self, text, height):
			if text is None:
				text = ""
			mc.text(
				self.installationHeadline,
				edit=True,
				height=height,
				label=text,
			)

		def spawnInstallationDetails(self, text=None):
			"""Create UI elements to display installation summary details"""
			if mc.layout(
				self.installationFrameLayout,
				query=True,
				numberOfChildren=True
			) == 0:

				if text is None:
					text = ""

				mc.columnLayout(
					parent=self.installationFrameLayout,
					adjustableColumn=1,
				)

				log = mc.scrollField(
					ww=True,
					editable=False,
					font='smallPlainLabelFont',
					text=text,
					height=10000, # Tall enough to never run out of height
				)

		def __str__(self):
			return self.panel

	class ButtonGroup(object):
		def __init__(self, owner, control_parent, alignBottom):
			self.buttonGroup = mc.rowLayout(
				numberOfColumns=3,
				adjustableColumn=1,
				parent=control_parent,
			)

			owner.spacer()

			self.back = mc.button(
				label="Go back",
				enable=False,
			)
			self.forward = mc.button(
				label="Continue",
			)

			mc.setParent('..')

			mc.formLayout(
				control_parent,
				edit=True,
				attachForm=[
					(self.buttonGroup, 'left', 5),
					(self.buttonGroup, 'bottom', 1),
					(self.buttonGroup, 'right', 5),
				],
				attachControl=[
					(alignBottom, 'bottom', 5, self.buttonGroup),
				],
			)
			mc.setParent('..')

		def backEnable(self):
			self._setBack(True)
		def backDisable(self):
			self._setBack(False)

		def forwardEnable(self):
			self._setForward(True)
		def forwardDisable(self):
			self._setForward(False)
		def forwardLabel(self, text):
			self._setForward(label=text)

		def _setBack(self, enable=None):
			if enable is not None:
				mc.button(
					self.back,
					edit=True,
					enable=enable,
				)
		def _setForward(self, enable=None, label=None):
			if enable is not None:
				mc.button(
					self.forward,
					edit=True,
					enable=enable,
				)
			if label is not None:
				width = mc.button(
					self.forward,
					query=True,
					width=True,
				)
				mc.button(
					self.forward,
					edit=True,
					label=label,
					width=width,
				)
		def __str__(self):
			return self.buttonGroup

	# Interface element generators
	def spacer(self, height=None, width=None):
		e = mc.text(
			label="",
		)
		if height:
			mc.text(
				e,
				edit=True,
				height=height,
			)
		if width:
			mc.text(
				e,
				edit=True,
				width=width,
			)

	def getPathDialog(self):
		L.warn( "This uses fileBrowserDialog which has been deprecated in 2011??" )
		maya.mel.eval( 'global string $FOUNDATION_FILEBROWSE = ""' )
		maya.mel.eval( 'global proc foundation_melBrowseCallback(string $path, string $type){ global string $FOUNDATION_FILEBROWSE; $FOUNDATION_FILEBROWSE = $path; }' )
		maya.mel.eval( 'global proc string foundation_melGetBrowsePath(){ global string $FOUNDATION_FILEBROWSE; return $FOUNDATION_FILEBROWSE; }' )
		maya.mel.eval( 'fileBrowser "foundation_melBrowseCallback" "Current Project" "" 4;' )
		path = maya.mel.eval( 'foundation_melGetBrowsePath()' )
		if path:
			return path

	class StepElement(object):
		def __init__(self, owner, parent, label, enable=None):
			self.panel = mc.rowLayout(
				numberOfColumns=2,
				columnWidth=[1,owner.prefs.pageEntryButtonSeparation],
				parent=parent,
			)
			#mc.radioCollection()
			self.radio = mc.radioButton(
				label="",
				editable=False,
				collection="steps",
			)
			mc.text(
				label=label,
				font='boldLabelFont',
			)
			mc.setParent('..')
			mc.setParent('..')

			if enable is not None:
				self._setStatus(enable)

		def disable(self):
			self._setStatus(False)
		def enable(self):
			self._setStatus(True)
		def _setStatus(self, bool):
			mc.layout(
				self.panel,
				edit=True,
				enable=bool,
			)
			if bool:
				L.debug( "Selecting radio button '%s'" % self.radio )
				mc.radioButton(
					self.radio,
					edit=True,
					select=True,
				)
		def __str__(self):
			return self.panel

	def _t(self):
		"""UI sanity test"""
		test = mc.text(label="test string ui object")
		if len( test.split("|") ) == 3:
			mc.text(test, edit=True, label="")
		else:
			print "Error in test:", test

	def bindButton(self, control, action):
		mc.button(
			control,
			edit=True,
			command=action
		)

	def bindTextFieldButtonGrp(self, control, button_action, change_action):
		mc.textFieldButtonGrp(
			control,
			edit=True,
			buttonCommand=button_action,
			changeCommand=change_action,
			forceChangeCommand=True,
		)

	def bindFrameLayout(self, control, pcc=None, pec=None):
		if pcc:
			mc.frameLayout(
				control,
				edit=True,
				preCollapseCommand=pcc,
			)
		if pec:
			mc.frameLayout(
				control,
				edit=True,
				preExpandCommand=pec,
			)


class Controller:
	def __init__(self):
		self.model = Model()
		self.view = View()
		self.page = 1

		self.bindEvents()
		self.subscribe()

		## HACKED AUTO PROGRESS ##
		#self._setPath("/Users/gaggle/Projects/Shared Script/")

	def bindEvents(self):
		"""Bind View elements to controller Events"""
		try:
			self.view.bindButton(
				self.view.introductionPanel.webbutton,
				self.GoToWebsite
			)

			self.view.bindButton(
				self.view.buttonGroup.back,
				self.GoBack
			)

			self.view.bindButton(
				self.view.buttonGroup.forward,
				self.GoForward
			)

			self.view.bindTextFieldButtonGrp(
				self.view.selectFolderPanel.sharedFolderButtonGroup,
				self.Browse,
				self.ChangePathField,
			)

			self.view.bindFrameLayout(
				self.view.summaryPanel.installationFrameLayout,
				pcc=self.InstallationDetailsCollapse,
				pec=self.InstallationDetailsExpand,
			)

		except:
			L.fatal( "Error during bindings" )
			raise

	def subscribe(self):
		"""Subscribe controller Events to Model messages"""
		try:
			obs.subscribe(self.PathChanged, "CHANGED FOLDER PATH")

			obs.subscribe(self.InstallSuccess, "INSTALLATION SUCCESSFUL")
			obs.subscribe(self.InstallFail, "INSTALLATION NO SUCH DIRECTORY")
			obs.subscribe(self.InstallError, "INSTALLATION ERROR")

			if L.isEnabledFor(logging.INFO):
				#Subscribe to all messages from the Model.
				obs.subscribe(self.printMessage)
		except:
			L.fatal( "Error during message subscription" )
			raise

	# === OUTBOUND COMMANDS === #
	def GoToWebsite(self, evt=None):
		self.model.openProductPage()

	def GoBack(self, evt=None):
		L.debug( "Controller says currentPage is '%s'..." % self.page )

		if self.page == 2:
			self._switchToStep1()
			self.page = self.page - 1
		else:
			raise Exception("Unknown page: %s" % self.page)

	def GoForward(self, evt=None):
		L.debug( "Controller says currentPage is '%s'..." % self.page )

		if self.page == 1:
			self._switchToStep2()
			self.page = self.page +1
		elif self.page == 2:
			if self.model.sharedFolderPath is not None:
				self._installClicked()
				self.page = self.page +1
		elif self.page == 3:
			L.debug( "Closing window" )
			self.view.closeWindow()
		else:
			raise Exception("Unknown page: %s" % self.page)

	def Browse(self, evt=None):
		"""Run when Browse button is clicked"""
		path = self.view.getPathDialog()
		if path is not None:
			self._setPath(path)

	def ChangePathField(self, evt=None):
		"""Run when PathField is changed"""
		self._updatePathFromPathField()

	def InstallationDetailsCollapse(self, evt=None):
		"""Run when InstallationDetail framelayout is collapsed"""
		self.view.summaryPanel.setInstallation_long( self.getInstallationStatus() )

	def InstallationDetailsExpand(self, evt=None):
		"""Run when InstallationDetail framelayout is expanded"""
		self.view.summaryPanel.setInstallation_short( self.getInstallationStatus() )

		self.view.summaryPanel.spawnInstallationDetails(
			self.model.getLog()
		)

	# === REACTIONS TO INCOMING MESSAGES === #
	def PathChanged(self, topic, action):
		"""React to CHANGED FOLDER PATH message"""
		self.view.selectFolderPanel.setPathLabel(action)
		self._autoSetForwardButtonStatus()
		if self.model.willWriteSharedUserSetup() or self.model.sharedUserSetupFile is None:
			self.view.selectFolderPanel.setNoFilesWrittenVisible(False)
		else:
			self.view.selectFolderPanel.setNoFilesWrittenVisible(True)

	def InstallSuccess(self, topic):
		"""React to INSTALLATION SUCCESSFUL message"""
		self._switchToStep3()

	def InstallFail(self, topic, exc):
		"""React to INSTALLATION NO SUCH DIRECTORY message"""
		mc.confirmDialog(
			title="Path error",
			message="Looking for path '%s' gave an error. Are you sure it's the path you meant to install to?\n\nPlease try again with a different path or contact your nearest technical artist or network administrator" % self.model.sharedFolderPath,
			button="OK",
			parent=self.view.prefs.window,
		)
		self.page += -1

	def InstallError(self, topic, exc):
		"""React to INSTALLATION ERROR message"""
		# We do nothing because this controller handles exceptions with a
		# try/except clause in the "_installClicked" function
		pass

	def printMessage(self, message, data=None):
		if data:
			L.info( "Controller received message '%s' containing: %s" % (message, data) )
		else:
			L.info( "Controller received message '%s'" % message )

	# === HELPER FUNCTIONS === #
	def getInstallationStatus(self):
		s = self.model.installationSuccess
		L.debug( "getInstallationStatus returns %s" % s )
		return s

	def exceptionHandler(self):
		formatted_exception = traceback.format_exc()
		L.warning( "Controller encountered exception: %s" % formatted_exception )
		self.model.addLog("Exception encountered:\n%s" % formatted_exception )

		self._switchToStep3(success=False)

	def _updatePathFromPathField(self):
		path = self.view.selectFolderPanel.getPathLabel()
		self._setPath(path)

	def _setPath(self, path):
		"""Set path variable in model"""
		self.model.setSharedFolderPath(path)

	def _switchToStep1(self, evt=None):
		"""Switch view to step1"""
		self.view.steps.step1()
		self.view.setResizeable(False)

		self.view.selectFolderPanel.setVisible(False)
		self.view.summaryPanel.setVisible(False)
		self.view.introductionPanel.setVisible(True)

		self.view.buttonGroup.backDisable()
		self.view.buttonGroup.forwardEnable()
		self.view.buttonGroup.forwardLabel("Continue")

	def _switchToStep2(self, evt=None):
		"""Switch view to step2"""
		self._updatePathFromPathField()
		self.view.steps.step2()
		self.view.setResizeable(False)

		self.view.introductionPanel.setVisible(False)
		self.view.summaryPanel.setVisible(False)
		self.view.selectFolderPanel.setVisible(True)

		self.view.buttonGroup.backEnable()
		self.view.buttonGroup.forwardLabel("Install")

		self.view.selectFolderPanel.setPathLabel(self.model.sharedFolderPath)
		self._autoSetForwardButtonStatus()

	def _installClicked(self, evt=None):
		"""Install button clicked"""
		try:
			self._updatePathFromPathField()
			self.model.doInstall()
		except:
			self.exceptionHandler()

	def _switchToStep3(self, evt=None, success=True):
		"""Switch view to step3. If success if False the window will turn Red
		and display text indicating installation failure"""
		self.view.steps.step3()
		self.view.setResizeable(True)

		self.view.introductionPanel.setVisible(False)
		self.view.selectFolderPanel.setVisible(False)
		self.view.summaryPanel.setVisible(True)

		self.view.buttonGroup.backDisable()
		self.view.buttonGroup.forwardLabel("Close")

		self.view.summaryPanel.setInstallationSuccess(success)

	def _autoSetForwardButtonStatus(self):
		"""Enable or disable Forward button based on model's sharedFolderPath"""
		if self.model.sharedFolderPath is not None:
			self.view.buttonGroup.forwardEnable()
		else:
			self.view.buttonGroup.forwardDisable()


class Model:
	def __init__(self):
		self.platform = getMayaPlatform()
		self.log = ""
		self.installationSuccess = None

		self.url = "http://foundation.jonlauridsen.com"
		self.userScriptDir = self.getUserScriptDir()
		self.userSetupFile = os.path.join(self.userScriptDir, "userSetup.py")
		self.foundationBootFile = os.path.join(self.userScriptDir, "foundationBoot.py")

		self.sharedFolderPath = None
		self.sharedUserSetupFile = None

	def doInstall(self):
		try:
			if self.willWriteSharedUserSetup():
				self._writeSharedUserSetup()
			self._writeOrAppendUserSetup()
			self._writeFoundationBoot()
		except IOError, e:
			L.warn( "IOError during install" )
			obs.emit("INSTALLATION NO SUCH DIRECTORY", traceback.format_exc())
			self.installationSuccess = False
		except Exception:
			L.warn( "Exception during install" )
			obs.emit("INSTALLATION ERROR", traceback.format_exc())
			self.installationSuccess = False

			# Generic exceptions are unexpected and by definition unhandled so
			# we end by raising them. The controller, if there is a controller,
			# should be able to handle generic exceptions in a sensible way for
			# the user.
			raise
		else:
			L.info( "Successful install" )
			obs.emit("INSTALLATION SUCCESSFUL")
			self.installationSuccess = True

	def openProductPage(self):
		webbrowser.open(self.url)
		obs.emit("OPENED PRODUCT PAGE", self.url)

	def setSharedFolderPath(self, path):
		if path is None or path == "":
			self.sharedFolderPath = None

			# Also update sharedUserSetupFile since it is based on the
			# sharedFolderPath
			self.sharedUserSetupFile = None
		else:
			validPath = self.getValidatedNaivePath(path)
			self.sharedFolderPath = validPath

			# Also update sharedUserSetupFile since it is based on the
			# sharedFolderPath
			self.sharedUserSetupFile = os.path.join(
				self.sharedFolderPath, "sharedUserSetup.py"
			)

		obs.emit("CHANGED FOLDER PATH", self.sharedFolderPath)

	def getValidatedNaivePath(self, path):
		"""Return naive (non-tested) path that is always a folder (ends with a
		forward slash)"""
		sPath = path.strip() # First we strip leading and trailing whitespaces
		sPath = sPath.replace("\\", "/")

		if sPath.endswith("/"):
			return sPath
		else:
			return sPath + "/"

	def getUserScriptDir(self):
		if self.platform == "windows":
			path = mc.internalVar(userPrefDir=True) + 'scripts/'
		elif self.platform == "mac":
			path = mc.internalVar(userScriptDir=True)
		L.debug( "Found script directory: '%s'" % path )
		return path

	def isUserSetupValid(self):
		#self._getUserSetupContent(getFilter=True) in self._readFile(self.userSetupFile)
		content = readFile(self.userSetupFile, getAsLines=True)
		filter = self._getUserSetupContent(getFilter=True)
		for l in content:
			if filter in l:
				if not l.startswith("#"):
					return True
		return False

	def _writeOrAppendUserSetup(self):
		if os.path.exists(self.userSetupFile):
			if self.isUserSetupValid():
				pass
				#self.addLog("Skipped file as it's already valid:\n%s" % self.userSetupFile)
			else:
				file = writeFile(
					self.userSetupFile, self._getUserSetupContent(), mode="a"
				)
				self.addLog("Appended boot information to file:\n%s" % self.userSetupFile)
				obs.emit("PROCESSED USER SETUP", file)

		else:
			file = writeFile(
				self.userSetupFile, self._getUserSetupContent()
			)
			self.addLog("Created file:\n%s" % file)
			obs.emit("PROCESSED USER SETUP", file)

	def _writeFoundationBoot(self):
		if os.path.exists(self.foundationBootFile):
			preexist = True
		else:
			preexist = False

		file = writeFile(
			self.foundationBootFile, self._getFoundationBootContent()
		)

		if preexist:
			self.addLog("Overwrote file:\n%s" % file)
		else:
			self.addLog("Created file:\n%s" % file)

		obs.emit("WROTE FOUNDATION BOOT", file)

	def _writeSharedUserSetup(self):
		file = writeFile(
			self.sharedUserSetupFile, self._getSharedUserSetupContent()
		)
		self.addLog("Created file:\n%s" % file)
		obs.emit("WROTE SHARED USER SETUP", file)

	def willWriteSharedUserSetup(self):
		if self.sharedUserSetupFile is None:
			return False

		if os.path.exists(self.sharedUserSetupFile):
			return False
		else:
			return True

	def _getUserSetupContent(self, getFilter=False):
		c = "import foundationBoot"
		additionalInfo = " # Initialize maya foundation booter. This line added %s" % (
			datetime.datetime.now()
		)
		if getFilter:
			return c
		return c + additionalInfo

	def _getFoundationBootContent(self):
		c = '''
		#!/usr/bin/env python
		#
		# foundation_boot.py
		# mayaPyTools
		#
		"""Bootstrap module for loading scripts from the Shared Scripting folder.
		Generated by the installer, edit at your own risk"""

		import sys, os

		def getToolPath():
			"""Return shared folder path.

			This variable is set through the installer"""
			path = '%s'
			return path

		def startModules():
			"""Look for sharedUserSetup.py and import it if possible"""
			try:
				import sharedUserSetup
			except ImportError, e:
				import traceback
				import maya.utils
				stack = traceback.format_exc()
				maya.utils.executeDeferred( reportErrorDuringLoad, e, stack )

		def reportErrorDuringLoad(e, stack):
			print stack,
			import maya.OpenMaya
			msg = "maya foundation failed to start: %%s" %% e
			maya.OpenMaya.MGlobal.displayError(msg)

		sys.path.append( getToolPath() )
		startModules()
		''' % self.sharedFolderPath
		return formatBlock(c)

	def _getSharedUserSetupContent(self):
		c = '''
		#!/usr/bin/env python
		#
		# sharedUserSetup.py
		# mayaPyTools
		"""sharedUserSetup.py acts like userSetup.py in that Maya executes any commands
		in the file during startup.

		The below text is copied from Maya's documentation:

		Maya runs any Python commands in the sharedUserSetup.py file whenever it starts
		up. You can use this file to set up your working environment or execute commonly
		used Python commands such as importing the maya.cmds module.

		The sharedUserSetup.py script is executed during the initialization and setup
		phase of Maya; therefore, only commands which set up your working environment
		and have no dependencies on Maya functionality can be successfully run in this
		script.

		Note: You can use maya.utils.executeDeferred() to delay code execution until
		after the Maya scene is initialized. For more information, see maya.utils.
		"""
		################################################################################
		# IMPORT BLOCK
		import maya.utils

		# Instantiate logger class
		import logging
		L = logging.getLogger( __name__ )
		L.setLevel(logging.INFO)
		if not L.handlers:
			ch = logging.StreamHandler()
			ch.setFormatter( logging.Formatter("%(name)s : %(levelname)s : %(message)s") )
			L.addHandler(ch)
		# HOW TO USE THE LOGGER:
		# Instead of "print" use the following code snippets:
		# L.debug("Debug message")
		# L.info("Info)
		# L.warn("A warning, but nothing we can't handle...")
		# L.error("An error has occured, time to take drastic measures")
		# L.fatal("A problem so huge we can't do anything but fail the entire program!")
		#
		# By changing the level of the logger you can decide how much information to
		# print out. E.g.:
		# L.setLevel(logging.DEBUG) - Logging messages above the setLevel threshhold
		# is printed, in this case all messages would be printed.

		################################################################################
		# FUNCTIONS BLOCK
		def executedDeferred():
			"""These commands are run after Maya is done initializing, so here we do
			have full access to Maya functionality"""
			#exampleFunction() # Uncomment this to run this function during startup
			reportLoaded()

		def reportLoaded():
			L.info( "Loaded" )

		def exampleFunction():
			"""Simple test function"""
			print "HELLO WORLD! You can see this message in the script output window"


		################################################################################
		# COMMANDS BLOCK
		maya.utils.executeDeferred( executedDeferred )
		'''
		return formatBlock(c)

	def addLog(self, entry):
		l = self.log
		if l:
			l = l + "\n\n"
		self.log = l + entry

	def getLog(self):
		return self.log


## HELPFUL FUNCTIONS ##
def readFile(filepath, getAsLines=False):
	"""Return content of filepath"""
	f = open(filepath, "r")
	try:
		if getAsLines:
			c = f.readlines()
		else:
			c = f.read()
	finally:
		f.close()
	return c

def writeFile(filepath, content, mode="w"):
	"""Write content to filepath. Return filepath"""
	f = open(filepath, mode)

	if mode == "a":
		content = "\n" + content

	try:
		f.write( content )
	finally:
		f.close()
	L.info( "Created file '%s'" % filepath )
	return filepath

def getMayaPlatform():
	"""Return platform as string: 'mac' or 'windows'"""
	if mc.about(windows=True):
		return "windows"
	elif mc.about(mac=True):
		return "mac"
	else:
		raise UnknownPlatformException()

## {{{ http://code.activestate.com/recipes/145672/ (r1)
def formatBlock(block):
	'''Format the given block of text, trimming leading/trailing
	empty lines and any leading whitespace that is common to all lines.
	The purpose is to let us list a code block as a multiline,
	triple-quoted Python string, taking care of indentation concerns.'''
	# separate block into lines
	lines = str(block).split('\n')
	# remove leading/trailing empty lines
	while lines and not lines[0]:  del lines[0]
	while lines and not lines[-1]: del lines[-1]
	# look at first line to see how much indentation to trim
	ws = re.match(r'\s*',lines[0]).group(0)
	if ws:
			lines = map( lambda x: x.replace(ws,'',1), lines )
	# remove leading/trailing blank lines (after leading ws removal)
	# we do this again in case there were pure-whitespace lines
	while lines and not lines[0]:  del lines[0]
	while lines and not lines[-1]: del lines[-1]
	return '\n'.join(lines)+'\n'
## end of http://code.activestate.com/recipes/145672/ }}}


## DEBUGGING FUNCTIONS ##
def _randColor(color=None):
	import random
	if color == "red":
		return [1,0,0]
	elif color == "green":
		return [0,1,0]
	elif color == "blue":
		return [0,0,1]
	else:
		r = random.random()
		g = random.random()
		b = random.random()
		return [r,g,b]


## MODULE SELF-LOADING FUNCTIONS ##
def wrapPyInMel(cmd):
	cmd = maya.cmds.encodeString(cmd)
	melcmd = 'python(\"' + cmd + '\")'
	return melcmd

def pathsplit( path ):
	basename = os.path.basename(path)
	dirname = os.path.dirname(path)
	exists = os.path.exists(path)

	if os.path.isdir(path) or basename is '':
		strtype = 'dir'
		result = {'type':strtype, 'exists':exists, 'path':dirname}
		return result
	elif os.path.isfile(path) or len(os.path.splitext(basename)) is 2:
		strtype = 'file'
		file = os.path.splitext(basename)[0]
		ext = os.path.splitext(basename)[1]
		result = {'type':strtype, 'exists':exists, 'path':dirname, 'file':file, 'ext':ext}
		return result
	else:
		raise Exception, "could not split path '" + path + "'"

def loadModule(module):
	try:
		filename = module.f_code.co_filename
		file = pathsplit(filename)['file']
	except AttributeError:
		if type(module) is str:
			file = module
		else:
			raise TypeError, "could not extract information from module of type '" + type(module).__name__ + "'. Provide a str or valid frame object"

	cmd = 'import ' + file
	melcmd = wrapPyInMel(cmd)

	try:
		maya.mel.eval(melcmd)
	except ImportError:
		raise ImportError, "module '" + file + "' failed to be imported"
	except RuntimeError:
		raise RuntimeError, "could not evaluate Py command '" + cmd + "'"
	return file

try:
	loadModule( sys._getframe() )
except (RuntimeError, AttributeError), e:
	print "Error loading module:", e, type(e)

try:
	controller = Controller()
except Exception, e:
	if L.isEnabledFor(logging.INFO):
		traceback.print_exc()
	print "Error initializing installation:", e, type(e)
