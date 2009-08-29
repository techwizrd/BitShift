#!/usr/bin/env python

import os, sys, gtk, git, time, urllib, hashlib, pango

from GtkSidebar import GtkSidebar

__thisdir__ = os.path.abspath(os.path.dirname(__file__))

class BottomBar(gtk.HBox):
	def __init__(self):
		gtk.HBox.__init__(self, False, 2)
		self.branches_l = gtk.Label("Branches: ")
		self.branches = gtk.combo_box_new_text()
		self.latest_b = gtk.Button("Latest", gtk.STOCK_REFRESH)
		self.next_b = gtk.Button("Next", gtk.STOCK_GO_FORWARD)
		self.previous_b = gtk.Button("Previous", gtk.STOCK_GO_BACK)
		
		self.pack_start(self.previous_b, False, False, 0)
		self.pack_start(self.latest_b, False, False, 0)
		self.pack_start(self.next_b, False, False, 0)
		self.pack_end(self.branches, False, False, 0)
		self.pack_end(self.branches_l, False, False, 0)
	
	def populate_branches(self, repo):
		for head in repo.branches:
			self.branches.append_text(head.name)

class CommitView(gtk.Notebook):
	def __init__(self):
		gtk.Notebook.__init__(self)
		self.set_show_tabs(False)
		
		self.vbox = gtk.VBox()
		self.add(self.vbox)
		
		self.textbuffer = gtk.TextBuffer()
		self.textview = gtk.TextView(self.textbuffer)
		self.vbox.add(self.textview)
		self.textbuffer.create_tag("c-message",
									weight = pango.WEIGHT_BOLD,
									wrap_mode = gtk.WRAP_WORD,
#									size = pango.SCALE_LARGE
									)
#		self.textbuffer.create_tag("c-hash")
		self.textbuffer.create_tag("c-time",
								justification = gtk.JUSTIFY_CENTER,
								style = pango.STYLE_ITALIC,
								underline = pango.UNDERLINE_SINGLE)
		
	def set_commit(self, commit):
		self.commit = commit
		self.textbuffer.set_text("")
		iter = self.textbuffer.get_iter_at_offset (0)
		self.textbuffer.insert_with_tags_by_name(iter, commit.message, "c-message")
		self.textbuffer.insert(iter, "\n" + commit.id)
		commit_time = "\n\n"+time.strftime("%c", self.commit.authored_date)
		self.textbuffer.insert_with_tags_by_name(iter, commit_time, "c-time")

class App:
	def __init__(self, gitdir=None):		
		self.window = gtk.Window()
		self.window.set_size_request(700,500)
		self.window.set_position(gtk.WIN_POS_CENTER)
		
		self.vbox = gtk.VBox(False, 0)
		self.window.add(self.vbox)
		
		self.hpaned = gtk.HPaned()
		self.vbox.add(self.hpaned)
		self.sidebar = GtkSidebar()
		self.hpaned.add(self.sidebar)
		self.commitview = CommitView()
		self.hpaned.add(self.commitview)
		self.hpaned.set_position(250)
		
		self.bottom_bar = BottomBar()
		
		self.gitdir = gitdir
		if gitdir != None:
			self.window.set_title("BitShift - " + os.path.abspath(self.gitdir))
			self.populate_sidebar(self.gitdir)
			self.bottom_bar.populate_branches(self.repo)
			self.bottom_bar.branches.set_active(0)
		else:
			self.window.set_title("BitShift")

		self.vbox.pack_end(self.bottom_bar, False, False, 0)
		
		self.main()
	
	def populate_sidebar(self, gitdir, branch = 'master', count = 100):
		self.repo = git.Repo(gitdir)
		self.commits = self.repo.commits(branch, max_count = count)
		for commit in self.commits:
			commit_time = time.strftime("%c", commit.authored_date)
			foo = commit.message.split('\n')
			if len(foo) > 1:
				text = "<b>%s ...</b>" % foo[0]
			else:
				text = "<b>%s</b>" % commit.message
			text += "\n<small>by %s on %s</small>" % (commit.author,
														commit_time)
			
			hashed = hashlib.md5(commit.author.email).hexdigest()
			image_path = "%s/grav_cache/%s.jpg" % (__thisdir__, hashed)
			if not os.path.exists(image_path):
				gravatar_url = "http://www.gravatar.com/avatar.php?"			
				gravatar_url += urllib.urlencode({'gravatar_id':hashed, 
													'size':str(40)})
				urllib.urlretrieve(gravatar_url, image_path)
				urllib.urlcleanup()
				
			image = gtk.gdk.pixbuf_new_from_file(image_path)

			self.sidebar.add_item(None,	[text, image])
	
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
	if not os.path.exists("%s/grav_cache" % __thisdir__):
		os.mkdir("%s/grav_cache" % __thisdir__)
	if len(sys.argv) < 2:
		gitdir = None
	else:
		gitdir = sys.argv[1]
	app = App(gitdir)
	gtk.main()
