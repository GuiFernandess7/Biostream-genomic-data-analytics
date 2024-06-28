use futures::SinkExt;
use tokio_tungstenite::connect_async;
use async_tungstenite::tungstenite::protocol::Message;
use futures::StreamExt;
use std::fs::OpenOptions;
use std::io::{self, Error, Read};
use std::path::Path;
use tokio::time::{timeout, Duration};
use dotenv::dotenv;
use std::env;
use env_logger;

#[tokio::main]
async fn main() {
    env_logger::init();

    if let Err(err) = dotenv() {
        eprintln!("Error loading .env file: {}", err);
    } else {
        println!(".env file loaded successfully");
    }

    let filepath = env::var("FASTA_FILE_PATH").expect("FILE_PATH not set in .env file");

    let (mut socket, response) = match connect_async("ws://localhost:8888/websocket").await {
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

    println!("Sending file content...");
    let chunk_size = 2 * 1024;
    let mut file = match get_file_as_byte_vec(filepath.as_str()) {
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

        let send_result = timeout(Duration::from_secs(30), socket.send(Message::Binary(chunk))).await;

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
        tokio::time::sleep(Duration::from_millis(500)).await;
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
