use futures::SinkExt;
use tokio_tungstenite::connect_async;
use async_tungstenite::tungstenite::protocol::Message;
use futures::StreamExt;
use std::fs::OpenOptions;
use std::io::{self, Error, Read};
use std::path::Path;
use tokio::time::{timeout, Duration};

#[tokio::main]
async fn main() {
    env_logger::init();

    let filepath = "./data/ncbi_dataset/data/GCF_025399875.1/GCF_025399875.1_Caltech_Dcor_3.1_genomic.fna";

    let (mut socket, response) = match connect_async("ws://localhost:8888/websocket/").await {
        Ok((s, r)) => (s, r),
        Err(e) => {
            eprintln!("Error connecting to server: {}", e);
            return;
        }
    };

    println!("Connected to the server");
    println!("Response HTTP code: {}", response.status());
    println!("Response contains the following headers:");
    for (header, value) in response.headers() {
        println!("* {}: {:?}", header, value);
    }

    //if let Err(e) = socket.send(Message::Text("Hello WebSocket".into())).await {
    //    eprintln!("Error sending message: {}", e);
    //    return;
    //}

    println!("Sending file content...");
    let chunk_size = 30 * 1024; // Define the size of each chunk (15KB in this case)
    let mut file = match get_file_as_byte_vec(filepath) {
        Ok(file) => file,
        Err(error) => {
            eprintln!("Error reading file: {}", error);
            return;
        }
    };

    while !file.is_empty() {
        let chunk: Vec<u8> = if file.len() > chunk_size {
            file.drain(..chunk_size).collect()
        } else {
            file.drain(..).collect()
        };

        let send_result = timeout(Duration::from_secs(10), socket.send(Message::Binary(chunk))).await;

        match send_result {
            Ok(Ok(())) => println!("Chunk sent successfully"),
            Ok(Err(e)) => {
                eprintln!("Error sending chunk: {}", e);
                break;
            }
            Err(_) => {
                eprintln!("Timeout sending chunk");
                break;
            }
        }

        // Adding a small delay to prevent overwhelming the server
        tokio::time::sleep(Duration::from_millis(50)).await;
    }

    println!("File sent successfully.");
}

fn get_file_as_byte_vec(filename: &str) -> Result<Vec<u8>, Error> {
    let mut file = OpenOptions::new()
        .read(true)
        .open(Path::new(filename))?;

    let metadata = file.metadata()?;
    let mut buffer = Vec::with_capacity(metadata.len() as usize);
    file.read_to_end(&mut buffer)?;
    Ok(buffer)
}
