/*
 * tree/align.rs
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

use regex::Regex;
use std::convert::TryFrom;

#[derive(Serialize, Deserialize, Debug, Copy, Clone, Hash, PartialEq, Eq)]
#[serde(rename_all = "kebab-case")]
pub enum Alignment {
    Left,
    Right,
    Center,
    Justify,
}

impl Alignment {
    pub fn name(self) -> &'static str {
        match self {
            Alignment::Left => "left",
            Alignment::Right => "right",
            Alignment::Center => "center",
            Alignment::Justify => "justify",
        }
    }
}

impl TryFrom<&'_ str> for Alignment {
    type Error = ();

    fn try_from(value: &str) -> Result<Self, Self::Error> {
        match value {
            "<" | "left" => Ok(Alignment::Left),
            ">" | "right" => Ok(Alignment::Right),
            "=" | "center" => Ok(Alignment::Center),
            "==" | "justify" => Ok(Alignment::Justify),
            _ => Err(()),
        }
    }
}

impl TryFrom<Option<&'_ str>> for Alignment {
    type Error = ();

    fn try_from(value: Option<&str>) -> Result<Self, Self::Error> {
        match value {
            Some(value) => Alignment::try_from(value),
            _ => Err(()),
        }
    }
}

#[derive(Serialize, Deserialize, Debug, Copy, Clone, PartialEq, Eq)]
#[serde(rename_all = "kebab-case")]
pub struct FloatAlignment {
    pub align: Alignment,
    pub float: bool,
}

impl FloatAlignment {
    pub fn parse(name: &str) -> Option<Self> {
        lazy_static! {
            static ref IMAGE_ALIGNMENT_REGEX: Regex =
                Regex::new(r"^[fF]?([<=>])").unwrap();
        }

        IMAGE_ALIGNMENT_REGEX
            .find(name)
            .and_then(|mtch| FloatAlignment::try_from(mtch.as_str()).ok())
    }
}

impl TryFrom<&'_ str> for FloatAlignment {
    type Error = ();

    fn try_from(value: &str) -> Result<Self, Self::Error> {
        let (align, float) = match value {
            "=" => (Alignment::Center, false),
            "<" => (Alignment::Left, false),
            ">" => (Alignment::Right, false),
            "f<" | "F<" => (Alignment::Left, true),
            "f>" | "F>" => (Alignment::Right, true),
            _ => return Err(()),
        };

        Ok(FloatAlignment { align, float })
    }
}