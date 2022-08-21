/*
 * url.rs
 *
 * ftml - Library to parse Wikidot text
 * Copyright (C) 2019-2022 Wikijump Team
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 */

use crate::tree::LinkLocation;
use std::borrow::Cow;
use regex::{RegexBuilder, Regex};
use wikidot_normalize::normalize;

pub const URL_SCHEMES: [&str; 20] = [
    "blob:",
    "chrome-extension://",
    "chrome://",
    "content://",
    "data:",
    "dns:",
    "feed:",
    "file://",
    "ftp://",
    "git://",
    "gopher://",
    "http://",
    "https://",
    "irc6://",
    "irc://",
    "ircs://",
    "mailto:",
    "resource://",
    "rtmp://",
    "sftp://",
];

lazy_static! {
    static ref URL_REGEX: Regex = {
        RegexBuilder::new(r"^[A-Za-z0-9$&+,/:;=?@%\-._~#]")
            .build()
            .unwrap()
    };
}

pub fn is_url(url: &str) -> bool {
    if url.contains('/') {
        return true
    }

    let lowered = url.to_lowercase();
    for scheme in &URL_SCHEMES {
        if lowered.starts_with(scheme) {
            return true;
        }
    }

    false
}

pub fn normalize_link<'a>(
    link: &'a LinkLocation<'a>,
    helper: &dyn BuildSiteUrl,
) -> Cow<'a, str> {
    match link {
        LinkLocation::Url(url) => normalize_href(url),
        LinkLocation::Page(page_ref) => {
            let (site, page) = page_ref.fields();

            match site {
                Some(site) => Cow::Owned(helper.build_url(site, page)),
                None => normalize_href(page),
            }
        }
    }
}

pub fn normalize_href(url: &str) -> Cow<str> {
    if is_url(url) || url.starts_with('#') || url.contains('/') || url.eq_ignore_ascii_case("javascript:;") {
        Cow::Borrowed(url)
    } else {
        let mut url = str!(url);
        normalize(&mut url);
        url.insert(0, '/');
        Cow::Owned(url)
    }
}

pub fn validate_href(url: &str) -> bool {
    // this attempts to match an URL that makes sense.
    // if it starts with a scheme, then it's definitely valid and allowed
    if is_url(url) {
        return true
    }
    // if it starts with a weird character, it's not valid and not allowed
    if !URL_REGEX.is_match(url) {
        return false
    }
    // if it starts with invalid protocol, it's not allowed
    let lowered = url.to_ascii_lowercase();
    if lowered != "javascript:;" && lowered.starts_with("javascript:") {
        return false
    }

    true
}

pub trait BuildSiteUrl {
    fn build_url(&self, site: &str, path: &str) -> String;
}
