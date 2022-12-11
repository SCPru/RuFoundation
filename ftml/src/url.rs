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
    static ref URL_STRICT_REGEX: Regex = {
        RegexBuilder::new(r"^(#[A-Za-z0-9_\-%]+|/[^/]+.*|[^/].*/.*|#)$")
            .build() 
            .unwrap()
    };
}

pub fn is_known_scheme(url: &str) -> bool {
    let lowered = url.to_lowercase();
    for scheme in &URL_SCHEMES {
        if lowered.starts_with(scheme) {
            return true;
        }
    }

    false
}

pub fn is_url(url: &str) -> bool {
    if url.contains('/') {
        return true
    }

    is_known_scheme(url)
}

pub fn normalize_link<'a>(link: &'a LinkLocation<'a>) -> Cow<'a, str> {
    match link {
        LinkLocation::Url(url) => normalize_href(url),
        LinkLocation::Page(page_ref, anchor) => {
            let normalized = if !page_ref.site().is_some() {
                Cow::Owned(normalize_href(&page_ref.to_string()).to_string())
            } else {
                panic!("Cross-site links are not supported")
            };

            match anchor {
                Some(anchor) => Cow::Owned(format!("#{anchor}")),
                None => normalized
            }
        }
    }
}

pub fn normalize_href(url: &str) -> Cow<str> {
    if is_url(url) || url.starts_with('#') || url.contains('/') || url.eq_ignore_ascii_case("javascript:;") {
        Cow::Borrowed(url)
    } else {
        let mut url = str!(url);
        url.insert(0, '/');
        Cow::Owned(url)
    }
}

pub fn validate_href(url: &str, strict: bool) -> bool {
    // disable cross-site hrefs for now
    if url.starts_with(':') {
        return false
    }
    // this attempts to match an URL that makes sense.
    // if it starts with a scheme, then it's definitely valid and allowed
    if is_known_scheme(url) {
        return true
    }
    // if it starts with a weird character, it's not valid and not allowed
    if !URL_REGEX.is_match(url) {
        return false
    }
    // if it starts with invalid protocol, it's not allowed
    let lowered = url.trim().to_ascii_lowercase();
    if lowered != "javascript:;" && lowered.starts_with("javascript:") {
        return false
    }
    if lowered.starts_with("data:") {
        return false
    }
    // strict mode is used to disambiguate between [##green|FORBIDDEN PLACE##] and [#anchor text on the anchor]
    if strict && !URL_STRICT_REGEX.is_match(url) {
        return false
    }

    true
}
