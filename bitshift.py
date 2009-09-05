#!/usr/bin/env python

import os
import sys
import gtk
import git
import time
import urllib
import hashlib
import pango
import gtksourceview

installdir = os.path.abspath(os.path.dirname(__file__))
__version__ = "0.01a"

class GtkSidebar(gtk.Frame):
    __gtype_name = 'GtkSidebar'
    def __init__(self):
        gtk.Frame.__init__(self)

        self.SBscrollbar = gtk.ScrolledWindow()
        self.SBscrollbar.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        self.SBstore = gtk.TreeStore(str, gtk.gdk.Pixbuf)
        self.SBtreeview = gtk.TreeView(self.SBstore)

        self.SBcolumn = gtk.TreeViewColumn('Pixbuf and Text')
        self.SBtreeview.append_column(self.SBcolumn)

        self.SBcell0 = gtk.CellRendererPixbuf()
        self.SBcell1 = gtk.CellRendererText()

        self.SBcolumn.pack_start(self.SBcell0, False)
        self.SBcolumn.pack_start(self.SBcell1, True)

        if gtk.gtk_version[1] < 2:
            self.SBcolumn.set_cell_data_func(self.SBcell0, self.make_pb)
        else:
            self.SBcolumn.set_attributes(self.SBcell0, pixbuf=1)#stock_id=1)
        self.SBcolumn.set_attributes(self.SBcell1, markup=0)

        self.SBtreeview.set_search_column(0)
        self.SBcolumn.set_sort_column_id(0)
        
        self.SBtreeview.set_headers_visible(False)

       # self.add(self.SBscrollbar)
        self.SBscrollbar.add(self.SBtreeview)

    def add_item(self, parent, stuff):
    	"""Add items to the model. If adding a large amount of items, decouple
    	first, add the items, and then recouple it."""
        return self.SBstore.append(parent, stuff)
    
    def decouple(self):
    	"""Used for decoupling the model. This is useful when adding large
    	amounts of rows, as you do not need to wait for each addition to
    	update the TreeView. Just remember to call recouple() afterwards."""
    	self.SBtreeview.set_model(None)
    
    def recouple(self):
    	"""Used for recoupling the model. This is useful when adding large
    	amounts of rows, as you do not need to wait for each addition to
    	update the TreeView."""
    	self.SBtreeview.set_model(self.SBstore)
    
    def make_pb(self, tvcolumn, cell, model, iter):
        stock = model.get_value(iter, 1)
        pb = self.SBtreeview.render_icon(stock, gtk.ICON_SIZE_MENU, None)
        cell.set_property('pixbuf', pb)
        return
    
    def get_store(self):
    	return self.SBstore
    	
    def clear(self):
    	self.decouple()
    	self.SBstore.clear()
    	self.recouple()

class BottomBar(gtk.HBox):
	def __init__(self):
		gtk.HBox.__init__(self, False, 2)
		self.branches_l = gtk.Label("Branches: ")
		self.branches = gtk.combo_box_new_text()
		self.latest_b = gtk.Button("Latest", gtk.STOCK_REFRESH)
		self.next_b = gtk.Button("Next", gtk.STOCK_GO_FORWARD)
		self.previous_b = gtk.Button("Previous", gtk.STOCK_GO_BACK)
		
		self.pack_start(self.previous_b, False, False, 0)
		#self.pack_start(self.latest_b, False, False, 0)
		self.pack_start(self.next_b, False, False, 0)
		self.pack_end(self.branches, False, False, 0)
		self.pack_end(self.branches_l, False, False, 0)
	
	def populate_branches(self, repo):
		for head in repo.branches:
			self.branches.append_text(head.name)

class DiffView(gtk.ScrolledWindow):
	def __init__(self):
		gtk.ScrolledWindow.__init__(self)
		self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		self.sourcebuffer = gtksourceview.SourceBuffer()
		self.sourceview = gtksourceview.SourceView(self.sourcebuffer)
		self.slm = gtksourceview.SourceLanguagesManager()
		self.language = self.slm.get_language_from_mime_type("text/x-patch")
		self.sourcebuffer.set_highlight(True)
		self.sourcebuffer.set_language(self.language)
		self.sourceview.set_show_line_numbers(True)
		self.sourceview.set_smart_home_end(True)
		self.sourceview.set_editable(False)
		self.add(self.sourceview)

class CommitView(gtk.VBox):
	def __init__(self):
		gtk.VBox.__init__(self)
		
		self.textbuffer = gtk.TextBuffer()
		self.textview = gtk.TextView(self.textbuffer)
		self.textview.set_editable(False)
		self.pack_start(self.textview, False, False, 0)
		self.diffview = DiffView()
		self.pack_end(self.diffview, True, True, 0)
		
		self.textbuffer.create_tag("c-message",
									weight = pango.WEIGHT_BOLD,
									wrap_mode = gtk.WRAP_WORD,)
		self.textbuffer.create_tag("c-time",
								justification = gtk.JUSTIFY_CENTER,
								style = pango.STYLE_ITALIC,
								underline = pango.UNDERLINE_SINGLE)
		
	def set_commit(self, commit):
		self.commit = commit
		self.set_commit_info(commit)
		self.set_diff_text(self.commit)
	
	def set_commit_info(self, commit):
		self.textbuffer.set_text("")
		iter = self.textbuffer.get_iter_at_offset (0)

		self.textbuffer.insert_with_tags_by_name(iter,
												commit.message,
												"c-message")
		self.textbuffer.insert(iter, "\n" + commit.id)
		commit_time = "\n\n%s\n" % time.strftime("%c",
												self.commit.authored_date)
		self.textbuffer.insert_with_tags_by_name(iter, commit_time, "c-time")

	def set_diff_text(self, commit):
#		difftext = ""
#		for diff in commit.diff(commit.repo, commit):
#			difftext += diff.diff + "\n"
		diff_list = commit.diff(commit.repo, commit)
		if diff_list != []:
#			difftext = diff_list[-1].diff
#			self.diffview.sourcebuffer.set_text(difftext)
			self.diffview.sourcebuffer.set_text(diff_list[-1].diff)

class App:
	def __init__(self, gitdir=None):		
		self.window = gtk.Window()
		self.window.set_size_request(700,500)
		self.window.set_position(gtk.WIN_POS_CENTER)
		
		self.initialize_menus()
		self.initialize_ui()

		if gitdir != None:
			self.set_gitdir(gitdir)
		else:
			self.window.set_title("BitShift")
		
		self.main()
	
	def initialize_ui(self):
		self.vbox = gtk.VBox(False, 0)
		self.window.add(self.vbox)
		self.vbox.pack_start(self.menubar, False, False, 0)
		self.hpaned = gtk.HPaned()
		self.vbox.add(self.hpaned)
		self.sidebar = GtkSidebar()
		self.hpaned.add(self.sidebar.SBscrollbar)
		self.commitview = CommitView()
		self.hpaned.add(self.commitview)
		self.hpaned.set_position(250)
		self.bottom_bar = BottomBar()
		self.vbox.pack_end(self.bottom_bar, False, False, 0)
	
	def initialize_menus(self):
		self.uimanager = gtk.UIManager()
		self.menuString = """<ui>
	<menubar name="MenuBar">
		<menu action="File">
			<menuitem action="Open"/>
			<separator name="sep3"/>
			<menuitem action="Quit"/>
		</menu>
		<menu action="Help">
			<menuitem action="About"/>
		</menu>
	</menubar>
</ui>"""
		try:
			self.uimanager.add_ui_from_string(self.menuString)
			self.actiongroup = gtk.ActionGroup('BitShift')
			self.actiongroup.add_actions([
										('Open', gtk.STOCK_OPEN, 'Open', None,
										"Open a File", self.open_repo),
										('Quit', gtk.STOCK_QUIT, '_Quit', None,
										 'Quit', gtk.main_quit),
										('File',None, '_File'),
										('About', gtk.STOCK_ABOUT,
										'_About', None,
										'About', self.show_about_dialog),
										('Help', None, '_Help')
										])
			self.uimanager.insert_action_group(self.actiongroup, 0)
			self.window.add_accel_group(self.uimanager.get_accel_group())
		except:
			print "menubar could not be initialized"
			raise SystemExit
		self.menubar = self.uimanager.get_widget("/MenuBar")
	
	def set_gitdir(self, gitdir):
		try:
			repo = git.Repo(gitdir)
		except git.InvalidGitRepositoryError:
				error_dialog = gtk.MessageDialog(parent=self.window,
									flags=0, type=gtk.MESSAGE_ERROR,
									buttons=gtk.BUTTONS_OK,
									message_format="Invalid Git Repository")
				stext = "%s is not a Git repository." % gitdir
				error_dialog.format_secondary_text(stext)
				response = error_dialog.run()
				if response == gtk.RESPONSE_OK:
					error_dialog.destroy()
					self.open_repo()
					return
				else:
					error_dialog.destroy()
					return
		self.gitdir = gitdir
		self.repo = repo
		self.populate_sidebar()
		self.bottom_bar.populate_branches(self.repo)
		self.bottom_bar.branches.set_active(0)	
		self.window.set_title("BitShift - " + os.path.abspath(self.gitdir))
	
	def populate_sidebar(self, branch = 'master', count = 50):
		self.commits = self.repo.commits(branch, max_count = count)
		for commit in self.commits:
			commit_time = time.strftime("%c", commit.authored_date)
			parts = commit.message.split('\n')
			if len(parts) > 1:
				text = "<b>%s ...</b>" % parts[0]
			else:
				text = "<b>%s</b>" % commit.message

			text += "\n<small>by %s on %s</small>" % (commit.author,
														commit_time)
			
			hashed = hashlib.md5(commit.author.email).hexdigest()
			image_path = "%s/grav_cache/%s.jpg" % (installdir, hashed)
			
			if not os.path.exists(image_path):
				gravatar_url = "http://www.gravatar.com/avatar.php?"			
				gravatar_url += urllib.urlencode({'gravatar_id':hashed, 
													'size':str(30)})
				urllib.urlretrieve(gravatar_url, image_path)
				urllib.urlcleanup()
				
			image = gtk.gdk.pixbuf_new_from_file(image_path)

			self.sidebar.add_item(None,	[text, image])
	
	def open_repo(self, widget=None):
		fc = gtk.FileChooserDialog(title='Open Git Repository...',
									parent=self.window,
									action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
									buttons=(gtk.STOCK_CANCEL,
										gtk.RESPONSE_CANCEL,
										gtk.STOCK_OPEN,
										gtk.RESPONSE_OK))
		fc.set_default_response(gtk.RESPONSE_OK)
		fc.run()
		if True:
			filedir = fc.get_filename()
		fc.destroy()
		self.set_gitdir(filedir)
		
	def show_about_dialog(self, widget):
		about = gtk.AboutDialog()
		about.set_name("KatByte")
		about.set_program_name("KatByte")
		about.set_version(__version__)
		about.set_comments("BitShift is a graphical Git client")
		about.set_copyright(u"Copyright (c) 2009 techwizrd")
		about.show_all()
	
	def react_commit(self, treeview):
		commit = self.commits[treeview.get_cursor()[0][0]]
		self.commitview.set_commit(commit)
	
	def branch_changed(self, combobox):
		self.sidebar.clear()
		branchname = combobox.get_active_text()
		self.populate_sidebar(self.gitdir, branchname)
	
	def get_latest_commits(self, button):
		os.system("cd %s && git pull" % self.gitdir)
		self.sidebar.clear()
		branchname = self.bottom_bar.branches.get_active_text()
		if branchname != None:
			self.populate_sidebar(self.gitdir, branchname)
		else:
			self.populate_sidebar(self.gitdir)
	
	def main(self):
		self.window.connect("delete-event", gtk.main_quit)
		self.sidebar.SBtreeview.connect("cursor-changed", self.react_commit)
		#self.bottom_bar.latest_b.connect("clicked", self.get_latest_commits)
		self.bottom_bar.branches.connect("changed", self.branch_changed)
		self.window.show_all()

if __name__ == "__main__":
	if not os.path.exists("%s/grav_cache" % installdir):
		os.mkdir("%s/grav_cache" % installdir)
	if len(sys.argv) < 2:
		gitdir = None
	else:
		gitdir = sys.argv[1]
	app = App(gitdir)
	gtk.main()
