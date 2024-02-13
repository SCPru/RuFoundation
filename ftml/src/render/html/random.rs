/*
 * render/html/random.rs
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

use rand::distributions::Alphanumeric;
use rand::prelude::*;
use std::iter;

#[derive(Debug)]
pub struct Random {
    rng: SmallRng,
}

impl Default for Random {
    #[inline]
    fn default() -> Self {
        let rng = SmallRng::from_entropy();

        Random { rng }
    }
}

impl Random {
    pub fn generate_html_id_into(&mut self, buffer: &mut String) {
        buffer.push_str("wj-id-");

        let char_stream = iter::repeat(())
            .map(|_| self.rng.sample(Alphanumeric))
            .map(char::from)
            .take(16);

        buffer.extend(char_stream);
    }

    pub fn generate_html_id(&mut self) -> String {
        let mut buffer = String::new();
        self.generate_html_id_into(&mut buffer);
        buffer
    }
}