import * as THREE from 'three';

import { UIPanel, UIRow, UINumber, UISpan, UIText } from './libs/ui.js';


function SidebarSound(editor) {
    const strings = editor.strings;
    const signals = editor.signals;
    const head_producer_states = new Map();

    const container = new UISpan();

    const panel = new UIPanel();
    panel.setBorderTop('0');
    panel.setPaddingTop('20px');
    container.add(panel);

    const row = new UIRow();
    row.add(new UIText("State").setWidth('90px'));
    const producer_state = new UIText().setWidth('50px');
    row.add(producer_state);
    panel.add(row);

    signals.addHead.add(function (object_config) {
        const object_id = object_config.id;
        const head_producer_state = new UIText().setWidth('50px');
        head_producer_state.setValue("");
        head_producer_states.set(object_id, head_producer_state); 
        const row = new UIRow();
        row.add(new UIText(object_id).setWidth('90px'));
        row.add(head_producer_state);
        panel.add(row);
    });

    signals.soundControllerUpdate.add(function (update) {
        producer_state.setValue(update.state);
        for (let i = 0; i < update.head_producers.length; i++) {
            let head_producer = update.head_producers[i];
            var head_producer_state = head_producer_states.get(head_producer.head_id);
            if (head_producer_state !== undefined) {
                // const value = JSON.stringify(head_producer)
                const value = head_producer.state
                head_producer_state.setValue(value);
            }
        }
    });

    function startSoundControllerWebSocketClient() {
        var ws = new WebSocket("ws://" + window.location.hostname + ":5681/");
        ws.onmessage = function (event) {
            var update = JSON.parse(event.data);
            signals.soundControllerUpdate.dispatch(update);
        };
        ws.onopen = function (event) {
            console.log('Sound Controller WebSocket connection opened.', event.reason);
        };
        ws.onclose = function (event) {
            console.log('Sound Controller WebSocket connection is closed. Reconnect will be attempted in 1 second.', event.reason);
            setTimeout(function () {
                startSoundControllerWebSocketClient();
            }, 1000);
        };
        ws.onerror = function (err) {
            ws.close();
        };
    }
    startSoundControllerWebSocketClient();

    return container;
}

export { SidebarSound };