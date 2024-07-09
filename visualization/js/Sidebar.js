import { UITabbedPanel, UISpan } from './libs/ui.js';

import { SidebarHeads } from './Sidebar.Heads.js';
import { SidebarLoadConfig } from './Sidebar.LoadConfig.js';
import { SidebarObject } from './Sidebar.Object.js';
import { SidebarSound } from './Sidebar.Sound.js';

function Sidebar(editor) {

	const strings = editor.strings;

	const container = new UITabbedPanel();
	container.setId( 'sidebar' );
    
    const heads = new SidebarHeads(editor);
    const config = new SidebarLoadConfig(editor);
    const object = new SidebarObject(editor);
    const sound = new SidebarSound(editor);

    container.addTab('heads', 'Heads', heads);
    container.addTab('sound', 'Sound', sound);
    // container.addTab('config', 'Config', config);
    // container.addTab('object', 'Object', object);
    container.select( 'heads' );

	return container;

}

export { Sidebar };
