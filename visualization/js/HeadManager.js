import * as THREE from 'three';


class Head {
    constructor() {
        this.id = null;
        this.orientation = null;
        this.center = null;
    }

    toJSON() {
        const output = {};
        output.id = this.id;
        output.orientation = this.orientation;
        output.center = this.center;
        return output;

    }
}

function HeadManager(editor) {
    const signals = editor.signals;
    const heads = new Map();

    function normalizeAngle(angle) {
        if (angle > 180.0) {
            angle = angle - 360.0;
        } else if (angle < -180.0) {
            angle = angle + 360.0;
        }
        return angle;
    }

    function getAngelFromQuaternion(q) {
        var angle = 2 * Math.acos(q.w);
        var s;
        if (1 - q.w * q.w < 0.000001) {
            // test to avoid divide by zero, s is always positive due to sqrt
            // if s close to zero then direction of axis not important
            // http://www.euclideanspace.com/maths/geometry/rotations/conversions/quaternionToAngle/
            s = 1;
        } else {
            s = Math.sqrt(1 - q.w * q.w);
        }
        const axis = new THREE.Vector3(q.x / s, q.y / s, q.z / s);
        
        if (axis.y < 0) {
            angle = 2.0 * Math.PI - angle;
        }
        return angle;
    }

    signals.refreshSidebarObject3D.add(function (object) {

        if (object !== editor.selected) return;

        var head = heads.get(object.name);
        if (head !== undefined) {
            const quaternion = new THREE.Quaternion();
            object.getWorldQuaternion(quaternion);
            const angle = getAngelFromQuaternion(quaternion) * THREE.MathUtils.RAD2DEG;
            head.orientation = normalizeAngle(angle - head.center);
            signals.headChanged.dispatch(head);
        }
    });

    signals.addHead.add(function (object_config) {
        const object_id = object_config.id;
        const orientation = object_config.orientation;
        var head = new Head();
        head.id = object_id;
        head.orientation = 0.0;
        head.center = orientation;
        heads.set(object_id, head);
    });

    // Start offering head state messages
    function startWebSocketForHeadStateMessages() {
        var ws = new WebSocket("ws://" + window.location.hostname + ":7892/");
        function onHeadChanged(head) {
            const event = {
                topic: head.id + '/orientation',
                value: head.orientation,
            };
            ws.send(JSON.stringify(event));
        };
        ws.onmessage = function (event) {
            const message = event.data;
            const response = toJSON();
            ws.send(JSON.stringify(response));
        };
        ws.onopen = function (event) {
            console.log('Heads state WebSocket opened.', event.reason);
            signals.headChanged.add(onHeadChanged);
            for (const head of heads.values()) {
                onHeadChanged(head);
            }
        };
        ws.onclose = function (event) {
            console.log('Head state WebSocket is closed. Reconnect will be attempted in 1 second.', event.reason);
            signals.headChanged.remove(onHeadChanged);
            setTimeout(function () {
                startWebSocketForHeadStateMessages();
            }, 1000);
        };
        ws.onerror = function (err) {
            ws.close();
        };
    }
    startWebSocketForHeadStateMessages();


    function toJSON() {
        const output = {};
        const heads_array = [];
        for (const value of heads.values()) {
            heads_array.push(value.toJSON());
        }
        output.heads = heads_array;
        return output;
    }

}




export { HeadManager };
