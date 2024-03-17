use std::time::{SystemTime, UNIX_EPOCH};
use std::collections::HashMap;
use secp256k1::{All, Secp256k1, PublicKey, SecretKey, Message};
use base64::{Engine as _, engine::general_purpose};
use sha2::{Sha256, Digest};

pub struct Signing {
    secp: Secp256k1<All>,
    huid: String,
    public_key: String,
    private_key: SecretKey,
}

impl Signing {
    pub fn new(huid: u32, api_token: &str) -> Self {
        let huid = huid.to_string();
        // decode the api key from base64
        let private_key_bytes = general_purpose::STANDARD.decode(api_token).unwrap();
        // parse the private key
        let private_key = SecretKey::from_slice(&private_key_bytes).unwrap();
        let secp = Secp256k1::new();
        // generate the public key from the private key
        let public_key = PublicKey::from_secret_key(&secp, &private_key);
        // serialize the public key
        let public_key_serialized = public_key.serialize();
        // take the first 33 bytes of the serialized public key
        let public_key_33bytes = &public_key_serialized[..33];
        // convert the public key to a hexadecimal string
        let public_key = hex::encode(public_key_33bytes);
        // return the Signing struct
        Self {
            secp,
            huid,
            public_key,
            private_key
        }
    }

    fn generate_signature(&self, ts: u64, path: &str, method: &str, payload: Option<&str>) -> String {
        let mut msg = format!("{}{}{}{}{}{}", ts.to_string().len(), ts, path.len(), path, method.len(), method);
        if let Some(payload) = payload {
            msg += &format!("{}{}", payload.len(), payload);
        }
        // hash the message with Sha256
        let msg_hash = Sha256::digest(msg.as_bytes());
        // parse the message hash to a Message
        let msg_parsed = Message::from_digest_slice(&msg_hash).unwrap();
        // sign the message with the private key
        let signature = self.secp.sign_ecdsa(&msg_parsed, &self.private_key);
        // serialize the signature to a compact format
        let signature_compact = signature.serialize_compact();
        // convert the signature to a hexadecimal string
        hex::encode(signature_compact)
    }

    fn get_ts(&self) -> u64 {
        let start = SystemTime::now();
        let since_the_epoch = start.duration_since(UNIX_EPOCH).unwrap();
        since_the_epoch.as_millis() as u64
    }

    pub fn get_auth_headers(&self, path: &str, method: &str, payload: Option<&str>) -> HashMap<String, String> {
        let ts = self.get_ts();
        let mut headers = HashMap::new();
        // fix the code below
        headers.insert("HM-CALLER".to_string(), self.huid.clone());
        headers.insert("HM-KEY".to_string(), self.public_key.clone());
        headers.insert("HM-TS".to_string(), ts.to_string());
        headers.insert("HM-SIGN".to_string(), self.generate_signature(ts, path, method, payload));
        headers
    }
}
