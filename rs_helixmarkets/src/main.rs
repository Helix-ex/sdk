mod signing;

fn main() {
    const HUID: u32 = 314207;
    const API_TOKEN: &str = "";

    let signing = signing::Signing::new(HUID, &API_TOKEN);
    let headers = signing.get_auth_headers("/funding", "GET", None);
    println!("{:?}", headers);
}
