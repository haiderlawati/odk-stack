/*
-- Raw Frame Sender --

This tool is used to create and send 'raw frames' to the ODK API.
See `app.models.schemas.frame.RawFrame` for the definition of a raw frame.
Written in NodeJS to stay close to the ODK APP functionality.

Usage:
$ node index.js garbage_images localhost 8000

- SFJ Guldemond, July 2020
*/

const WebSocket = require('ws');
const fs = require('fs');

// Handle command line arguments
const args = process.argv.slice(2);
const imageFolder = args[0];
const host = args[1] || 'localhost';
const port = args[2] || '8080';

const wsUrl = "ws://" + host + ":" + port + "/stream";
const ws = new WebSocket(wsUrl);
console.log("Connection set to: ", wsUrl);

function base64Encode(file) {
    var bitmap = fs.readFileSync(file);
    return new Buffer(bitmap).toString('base64');
}

function createFrame(imagePath, fileName) {
    const base64Img = base64Encode(imagePath);

    const now = new Date();

    date_options = {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    };

    const formattedDate = now.toLocaleString('nl-NL', date_options);

    const frameData = {
        img: base64Img,
        stream_id: 'foobar',
        user_type: 'foobar',
        vehicle_type: 'foobar',
        user_id: '9999',
        lng: 4.901060,
        lat: 52.367867,
        timestamp: formattedDate,
    };
    return frameData;
}

function sendFrames() {
    const folderPath = imageFolder;
    const fullPath = fs.realpathSync(folderPath) + "/";
    const files = fs.readdirSync(fullPath);

    for (let i in files) {
        setTimeout(function() {
            const frameData = createFrame(fullPath + files[i], files[i]);
            ws.send(JSON.stringify(frameData));
            console.log("Frame sent")
        }, i*2000);
    }
}

ws.on('open', function open() {
    sendFrames();
})

ws.on('message', function incoming(data) {
    console.log(data);
})
